"""Modelo base con clave primaria UUID."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlmodel import Field

from .base_model import BaseModel


class BaseUUIDModel(BaseModel):
    """Entidad con `id` UUID generado automáticamente."""

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
