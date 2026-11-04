"""Acceso a las recomendaciones precalculadas."""

from __future__ import annotations

from sqlmodel import col, select

from ..database.models import Recommendation, RecommenderModel
from .base_repository import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repositorio de `Recommendation`."""

    _entity_class = Recommendation

    async def get_top_k(
        self, user_id: str, model: RecommenderModel, k: int
    ) -> list[Recommendation]:
        """Las `k` primeras recomendaciones de `model` para el usuario, por posición."""
        result = await self._session.exec(
            select(Recommendation)
            .where(Recommendation.user_id == user_id, Recommendation.model == model)
            .order_by(col(Recommendation.rank))
            .limit(k)
        )
        return list(result.all())
