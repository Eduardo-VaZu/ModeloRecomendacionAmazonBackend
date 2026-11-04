"""Reseña de un usuario sobre un producto."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field

from .base import BaseUUIDModel
from .enums import DataSplit


class Interaction(BaseUUIDModel, table=True):
    """Interacción explícita (rating) con su partición temporal."""

    user_id: str = Field(max_length=64, index=True)
    product_id: str = Field(max_length=32)
    rating: float = Field(ge=1, le=5)
    reviewed_at: datetime = Field(sa_type=DateTime(timezone=True))
    split: DataSplit
