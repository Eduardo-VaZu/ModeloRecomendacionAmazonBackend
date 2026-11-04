"""Usuario incluido en la muestra del prototipo."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel


class DemoUser(BaseUUIDModel, table=True):
    """Usuario activo (al menos 5 interacciones) exportado por el pipeline."""

    user_id: str = Field(max_length=64, unique=True, index=True)
    n_interactions: int = Field(ge=1)
