"""Resumen del dataset con el que se generó el paquete demo."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel


class DatasetSummary(BaseUUIDModel, table=True):
    """Origen y tamaño del dataset; `is_synthetic` marca datos de desarrollo."""

    source: str = Field(max_length=128)
    category: str = Field(max_length=64)
    is_synthetic: bool
    n_users: int = Field(ge=0)
    n_items: int = Field(ge=0)
    n_interactions: int = Field(ge=0)
    n_candidates: int = Field(ge=1)
