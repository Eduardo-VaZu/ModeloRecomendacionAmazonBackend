"""Base de los DTO: snake_case en Python, camelCase en JSON."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseDataTransfer(BaseModel):
    """DTO construible desde entidades ORM y serializado en camelCase."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class NoRequest(BaseDataTransfer):
    """Petición vacía para casos de uso sin parámetros."""
