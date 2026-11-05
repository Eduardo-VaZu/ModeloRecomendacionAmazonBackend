"""Valor de una métrica de evaluación para un modelo."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel
from .enums import RecommenderModel


class ExperimentResult(BaseUUIDModel, table=True):
    """Métrica de evaluación de un modelo, tal como la escribe `05_evaluate`.

    Con K: precision (I7), recall (I8), ndcg (I9), mrr (I10), coverage (I11), ild (I12), f1.
    Sin K: rmse, mae, train_time_s, n_users_evaluated.
    """

    model: RecommenderModel
    metric: str = Field(max_length=32)
    k: int | None = Field(default=None, ge=1)
    value: float
