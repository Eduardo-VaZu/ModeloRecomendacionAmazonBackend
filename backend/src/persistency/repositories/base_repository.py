"""CRUD genérico sobre la sesión activa de la unidad de trabajo."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlmodel import SQLModel, delete, select
from sqlmodel.ext.asyncio.session import AsyncSession


class BaseRepository[TEntity: SQLModel]:
    """Repositorio base; las subclases solo definen `_entity_class`."""

    _entity_class: type[TEntity]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[TEntity]:
        """Todas las filas de la tabla."""
        result = await self._session.exec(select(self._entity_class))
        return list(result.all())

    async def get_by_id(self, entity_id: UUID) -> TEntity | None:
        """Fila por clave primaria, o `None` si no existe."""
        return await self._session.get(self._entity_class, entity_id)

    async def create(self, entity: TEntity) -> TEntity:
        """Inserta una fila y la devuelve con los valores generados por la base de datos."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: TEntity) -> TEntity:
        """Persiste los cambios de una fila existente."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: TEntity) -> None:
        """Elimina una fila."""
        await self._session.delete(entity)
        await self._session.flush()

    async def bulk_create(self, entities: Sequence[TEntity]) -> None:
        """Inserta muchas filas en una sola operación."""
        self._session.add_all(entities)
        await self._session.flush()

    async def delete_all(self) -> None:
        """Vacía la tabla (usado al reimportar el paquete demo)."""
        await self._session.exec(delete(self._entity_class))
