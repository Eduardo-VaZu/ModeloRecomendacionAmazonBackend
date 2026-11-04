"""Recomendación precalculada por el pipeline para un usuario y un modelo."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel
from .enums import RecommenderModel


class Recommendation(BaseUUIDModel, table=True):
    """Producto en la posición `rank` del Top-K de un modelo, con sus puntajes por etapa."""

    user_id: str = Field(max_length=64, index=True)
    model: RecommenderModel = Field(index=True)
    rank: int = Field(ge=1)
    product_id: str = Field(max_length=32)
    content_score: float | None = None
    als_score: float | None = None
    final_score: float
    is_hit: bool
    reason_product_id: str | None = Field(default=None, max_length=32)
