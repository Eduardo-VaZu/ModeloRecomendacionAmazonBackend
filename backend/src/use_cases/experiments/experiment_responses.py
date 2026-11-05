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


class HypothesisTestResponse(BaseDataTransfer):
    """Contraste O1 vs. O2 de un indicador con un corte K."""

    hypothesis: str
    indicator: str
    metric: str
    k: int
    n_pairs: int
    mean_o1: float
    mean_o2: float
    relative_improvement: float
    n_improved: int
    n_tied: int
    n_worse: int
    shapiro_p: float | None
    test: str
    statistic: float | None
    p_value: float
    effect_size: float | None
    effect_size_name: str
    effect_magnitude: str
    significant: bool
    meets_goal: bool


class HypothesisTestsResponse(BaseDataTransfer):
    """Pruebas de HE1-HE3, ordenadas por hipótesis, indicador y K."""

    items: list[HypothesisTestResponse]


class ViIndicatorResponse(BaseDataTransfer):
    """Indicador de la variable independiente (k solo en I6)."""

    dimension: str
    indicator: str
    name: str
    k: int | None
    value: float


class ViIndicatorsResponse(BaseDataTransfer):
    """Indicadores I1-I6 del sistema híbrido."""

    items: list[ViIndicatorResponse]


class DatasetSummaryResponse(BaseDataTransfer):
    """Origen y tamaño del dataset del prototipo."""

    source: str
    category: str
    is_synthetic: bool
    n_users: int
    n_items: int
    n_interactions: int
    n_candidates: int
