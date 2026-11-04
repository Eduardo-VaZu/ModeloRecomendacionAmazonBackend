"""Acceso a los usuarios de la muestra."""

from __future__ import annotations

from sqlmodel import col, func, select

from ..database.models import DemoUser
from .base_repository import BaseRepository


class DemoUserRepository(BaseRepository[DemoUser]):
    """Repositorio de `DemoUser`."""

    _entity_class = DemoUser

    async def get_by_user_id(self, user_id: str) -> DemoUser | None:
        """Usuario por su identificador de Amazon."""
        result = await self._session.exec(select(DemoUser).where(DemoUser.user_id == user_id))
        return result.first()

    async def search(
        self, query: str | None, limit: int, offset: int
    ) -> tuple[list[DemoUser], int]:
        """Página de usuarios cuyo id contiene `query`, más el total de coincidencias."""
        statement = select(DemoUser)
        if query:
            statement = statement.where(col(DemoUser.user_id).icontains(query))
        total = await self._session.exec(select(func.count()).select_from(statement.subquery()))
        page = await self._session.exec(
            statement.order_by(col(DemoUser.n_interactions).desc(), col(DemoUser.user_id))
            .limit(limit)
            .offset(offset)
        )
        return list(page.all()), total.one()
