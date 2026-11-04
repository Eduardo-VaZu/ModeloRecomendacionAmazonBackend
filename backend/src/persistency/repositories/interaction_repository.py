"""Acceso al historial de interacciones."""

from __future__ import annotations

from sqlmodel import col, select

from ..database.models import Interaction
from .base_repository import BaseRepository


class InteractionRepository(BaseRepository[Interaction]):
    """Repositorio de `Interaction`."""

    _entity_class = Interaction

    async def get_by_user(self, user_id: str) -> list[Interaction]:
        """Historial del usuario en orden cronológico."""
        result = await self._session.exec(
            select(Interaction)
            .where(Interaction.user_id == user_id)
            .order_by(col(Interaction.reviewed_at))
        )
        return list(result.all())
