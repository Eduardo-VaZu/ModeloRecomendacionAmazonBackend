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
    Interaction,
    Product,
    Recommendation,
    RecommenderModel,
)
from ..persistency.unit_of_work import UnitOfWork

TABLES = (
    "dataset_summary",
    "product",
    "demo_user",
    "interaction",
    "recommendation",
    "experiment_result",
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
        await unit.commit()
