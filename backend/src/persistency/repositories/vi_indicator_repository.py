"""Acceso a los indicadores de la variable independiente."""

from __future__ import annotations

from ..database.models import ViIndicator
from .base_repository import BaseRepository


class ViIndicatorRepository(BaseRepository[ViIndicator]):
    """Repositorio de `ViIndicator`."""

    _entity_class = ViIndicator
