"""Acceso a los resultados de la evaluación."""

from __future__ import annotations

from ..database.models import ExperimentResult
from .base_repository import BaseRepository


class ExperimentResultRepository(BaseRepository[ExperimentResult]):
    """Repositorio de `ExperimentResult`."""

    _entity_class = ExperimentResult
