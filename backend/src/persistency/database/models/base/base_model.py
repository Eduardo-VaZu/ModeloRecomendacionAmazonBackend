"""Modelo base: el nombre de la tabla se deriva del nombre de la clase."""

from __future__ import annotations

from sqlalchemy.orm import declared_attr
from sqlmodel import SQLModel

from .snake_case import snake_case


class BaseModel(SQLModel):
    """Base de todas las entidades persistidas."""

    @declared_attr  # type: ignore[misc]
    def __tablename__(cls) -> str:  # noqa: N805
        """Tabla en snake_case a partir del nombre de la clase."""
        return snake_case(cls.__name__)
