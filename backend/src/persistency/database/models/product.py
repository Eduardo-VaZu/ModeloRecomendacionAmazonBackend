"""Producto del catálogo de Amazon."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel


class Product(BaseUUIDModel, table=True):
    """Producto identificado por su `parent_asin` de Amazon Reviews 2023."""

    product_id: str = Field(max_length=32, unique=True, index=True)
    title: str
    category: str = Field(default="", max_length=128)
    store: str | None = Field(default=None, max_length=256)
