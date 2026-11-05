"""Fixtures de integración: cliente HTTP sobre la app y limpieza de tablas."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from ..database import session_factory
from ..main import app
from ..persistency.database.models import (
    DatasetSummary,
    DataSplit,
    DemoUser,
    ExperimentResult,
    HypothesisTest,
    Interaction,
    Product,
    Recommendation,
    RecommenderModel,
    ViIndicator,
)
from ..persistency.unit_of_work import UnitOfWork

TABLES = (
    "dataset_summary",
    "product",
    "demo_user",
    "interaction",
    "recommendation",
    "experiment_result",
    "hypothesis_test",
    "vi_indicator",
)


@pytest.fixture
async def http_client() -> AsyncIterator[AsyncClient]:
    """Cliente que llama a la app en memoria (sin red)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def _truncate_tables() -> None:
    async with session_factory() as session:
        await session.exec(text(f"TRUNCATE {', '.join(TABLES)}"))  # type: ignore[call-overload]
        await session.commit()


@pytest.fixture(autouse=True)
async def clean_tables() -> AsyncIterator[None]:
    """Vacía las tablas del prototipo antes y después de cada test (aísla de datos sembrados)."""
    await _truncate_tables()
    yield
    await _truncate_tables()


@pytest.fixture
async def demo_data() -> None:
    """Un usuario con historial, recomendaciones O1/Etapa 1/O2 y una métrica."""
    async with session_factory() as session:
        unit = UnitOfWork(session)
        await unit.dataset_summaries.create(
            DatasetSummary(
                source="test",
                category="Video_Games",
                is_synthetic=True,
                n_users=1,
                n_items=3,
                n_interactions=1,
                n_candidates=300,
            )
        )
        await unit.products.bulk_create(
            [
                Product(product_id=f"P{i}", title=f"Producto {i}", category="Juegos")
                for i in range(3)
            ]
        )
        await unit.demo_users.bulk_create([DemoUser(user_id="U1", n_interactions=5)])
        await unit.interactions.bulk_create(
            [
                Interaction(
                    user_id="U1",
                    product_id="P0",
                    rating=5,
                    reviewed_at=datetime(2023, 1, 1, tzinfo=UTC),
                    split=DataSplit.TRAIN,
                )
            ]
        )
        await unit.recommendations.bulk_create(
            [
                Recommendation(
                    user_id="U1",
                    model=RecommenderModel.POPULARITY,
                    rank=1,
                    product_id="P1",
                    final_score=10,
                    is_hit=False,
                ),
                Recommendation(
                    user_id="U1",
                    model=RecommenderModel.CONTENT_BASED,
                    rank=1,
                    product_id="P1",
                    content_score=0.9,
                    final_score=0.9,
                    is_hit=False,
                    reason_product_id="P0",
                ),
                Recommendation(
                    user_id="U1",
                    model=RecommenderModel.CONTENT_BASED,
                    rank=2,
                    product_id="P2",
                    content_score=0.8,
                    final_score=0.8,
                    is_hit=True,
                    reason_product_id="P0",
                ),
                Recommendation(
                    user_id="U1",
                    model=RecommenderModel.HYBRID,
                    rank=1,
                    product_id="P2",
                    content_score=0.8,
                    als_score=0.95,
                    final_score=0.9,
                    is_hit=True,
                    reason_product_id="P0",
                ),
            ]
        )
        await unit.experiment_results.bulk_create(
            [ExperimentResult(model=RecommenderModel.HYBRID, metric="rmse", value=0.95)]
        )
        await unit.hypothesis_tests.bulk_create(
            [
                _hypothesis_test("HE3", "I12", "ild", 10, -0.09, meets_goal=False),
                _hypothesis_test("HE1", "I7", "precision", 10, 1.89, meets_goal=True),
                _hypothesis_test("HE1", "I7", "precision", 5, 1.44, meets_goal=True),
            ]
        )
        await unit.vi_indicators.bulk_create(
            [
                ViIndicator(dimension="D3", indicator="I6", name="Tasa", k=10, value=0.46),
                ViIndicator(dimension="D1", indicator="I1", name="Atributos", value=5),
            ]
        )
        await unit.commit()


def _hypothesis_test(
    hypothesis: str, indicator: str, metric: str, k: int, improvement: float, *, meets_goal: bool
) -> HypothesisTest:
    """Prueba de hipótesis mínima para los tests."""
    return HypothesisTest(
        hypothesis=hypothesis,
        indicator=indicator,
        metric=f"{metric}@{k}",
        k=k,
        n_pairs=100,
        mean_o1=0.01,
        mean_o2=0.01 * (1 + improvement),
        relative_improvement=improvement,
        n_improved=10,
        n_tied=85,
        n_worse=5,
        shapiro_p=1e-20,
        test="Wilcoxon rangos con signo",
        statistic=300.0,
        p_value=1e-5 if meets_goal else 1.0,
        effect_size=0.45 if meets_goal else -0.8,
        effect_size_name="r",
        effect_magnitude="mediano" if meets_goal else "grande",
        significant=meets_goal,
        meets_goal=meets_goal,
    )
