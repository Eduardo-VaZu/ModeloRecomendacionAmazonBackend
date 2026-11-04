"""Respuestas de los casos de uso de resultados experimentales."""

from __future__ import annotations

from ...persistency.database.models import RecommenderModel
from ..shared.base_data_transfer import BaseDataTransfer


class ExperimentResultResponse(BaseDataTransfer):
    """Valor de una métrica para un modelo (k = None en métricas sin corte)."""

    model: RecommenderModel
    metric: str
    k: int | None
    value: float


class ExperimentResultsResponse(BaseDataTransfer):
    """Todas las métricas de todos los modelos."""

    items: list[ExperimentResultResponse]


class DatasetSummaryResponse(BaseDataTransfer):
    """Origen y tamaño del dataset del prototipo."""

    source: str
    category: str
    is_synthetic: bool
    n_users: int
    n_items: int
    n_interactions: int
    n_candidates: int
