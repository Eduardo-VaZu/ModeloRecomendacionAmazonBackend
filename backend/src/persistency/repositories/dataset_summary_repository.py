"""Acceso al resumen del dataset."""

from __future__ import annotations

from sqlmodel import select

from ..database.models import DatasetSummary
from .base_repository import BaseRepository


class DatasetSummaryRepository(BaseRepository[DatasetSummary]):
    """Repositorio de `DatasetSummary` (una sola fila por paquete importado)."""

    _entity_class = DatasetSummary

    async def get_current(self) -> DatasetSummary | None:
        """Resumen del paquete importado, o `None` si aún no se importó ninguno."""
        result = await self._session.exec(select(DatasetSummary).limit(1))
        return result.first()
