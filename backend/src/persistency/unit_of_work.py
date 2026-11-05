"""Agrupa todos los repositorios sobre una misma sesión (una transacción)."""

from __future__ import annotations

from sqlmodel.ext.asyncio.session import AsyncSession

from .repositories.dataset_summary_repository import DatasetSummaryRepository
from .repositories.demo_user_repository import DemoUserRepository
from .repositories.experiment_result_repository import ExperimentResultRepository
from .repositories.hypothesis_test_repository import HypothesisTestRepository
from .repositories.interaction_repository import InteractionRepository
from .repositories.product_repository import ProductRepository
from .repositories.recommendation_repository import RecommendationRepository
from .repositories.vi_indicator_repository import ViIndicatorRepository


class UnitOfWork:
    """Repositorios que comparten la sesión de la petición."""

    dataset_summaries: DatasetSummaryRepository
    products: ProductRepository
    demo_users: DemoUserRepository
    interactions: InteractionRepository
    recommendations: RecommendationRepository
    experiment_results: ExperimentResultRepository
    hypothesis_tests: HypothesisTestRepository
    vi_indicators: ViIndicatorRepository

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.dataset_summaries = DatasetSummaryRepository(session)
        self.products = ProductRepository(session)
        self.demo_users = DemoUserRepository(session)
        self.interactions = InteractionRepository(session)
        self.recommendations = RecommendationRepository(session)
        self.experiment_results = ExperimentResultRepository(session)
        self.hypothesis_tests = HypothesisTestRepository(session)
        self.vi_indicators = ViIndicatorRepository(session)

    async def commit(self) -> None:
        """Confirma la transacción."""
        await self._session.commit()
