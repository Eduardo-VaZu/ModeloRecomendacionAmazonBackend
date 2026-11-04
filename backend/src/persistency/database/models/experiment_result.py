"""Valor de una métrica de evaluación para un modelo."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel
from .enums import RecommenderModel


class ExperimentResult(BaseUUIDModel, table=True):
    """Métrica (RMSE, MAE, precision, recall, f1, coverage, train_time_s) de un modelo."""

    model: RecommenderModel
    metric: str = Field(max_length=32)
    k: int | None = Field(default=None, ge=1)
    value: float
