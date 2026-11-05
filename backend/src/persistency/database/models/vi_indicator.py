"""Indicador de la variable independiente (I1-I6) del sistema híbrido."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel


class ViIndicator(BaseUUIDModel, table=True):
    """Parámetro de diseño (I1-I5) o tasa de hibridación del ranking (I6, una fila por K)."""

    dimension: str = Field(max_length=8)
    """D1 (contenido), D2 (ALS) o D3 (hibridación)."""
    indicator: str = Field(max_length=8)
    """I1 a I6."""
    name: str = Field(max_length=128)
    k: int | None = Field(default=None, ge=1)
    """Solo I6 depende del corte K."""
    value: float
