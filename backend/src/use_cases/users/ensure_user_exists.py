"""Validación compartida por los casos de uso de un usuario concreto."""

from __future__ import annotations

from ...persistency.unit_of_work import UnitOfWork
from ..shared.errors import NotFoundError


async def ensure_user_exists(unit_of_work: UnitOfWork, user_id: str) -> None:
    """Lanza `NotFoundError` si el usuario no está en la muestra (p. ej., cold start)."""
    if await unit_of_work.demo_users.get_by_user_id(user_id) is None:
        raise NotFoundError(f"El usuario '{user_id}' no está en la muestra del prototipo")
