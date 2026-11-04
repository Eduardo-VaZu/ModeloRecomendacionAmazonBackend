"""Acceso al catálogo de productos."""

from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import col, select

from ..database.models import Product
from .base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repositorio de `Product`."""

    _entity_class = Product

    async def get_map(self, product_ids: Iterable[str]) -> dict[str, Product]:
        """Productos indexados por `product_id` (los inexistentes se omiten)."""
        ids = set(product_ids)
        if not ids:
            return {}
        result = await self._session.exec(select(Product).where(col(Product.product_id).in_(ids)))
        return {product.product_id: product for product in result.all()}
