"""Caso de uso: historial de un usuario."""

from __future__ import annotations

from ..shared.base_handler import BaseHandler
from .ensure_user_exists import ensure_user_exists
from .user_requests import GetUserHistoryRequest
from .user_responses import InteractionResponse, ProductResponse, UserHistoryResponse


class GetUserHistoryHandler(BaseHandler[GetUserHistoryRequest, UserHistoryResponse]):
    """Devuelve las reseñas del usuario con los datos de cada producto."""

    async def execute(self, request: GetUserHistoryRequest) -> UserHistoryResponse:
        await ensure_user_exists(self._unit_of_work, request.user_id)
        interactions = await self._unit_of_work.interactions.get_by_user(request.user_id)
        products = await self._unit_of_work.products.get_map(i.product_id for i in interactions)
        return UserHistoryResponse(
            user_id=request.user_id,
            interactions=[
                InteractionResponse(
                    product=ProductResponse.from_map(products, interaction.product_id),
                    rating=interaction.rating,
                    reviewed_at=interaction.reviewed_at,
                    split=interaction.split,
                )
                for interaction in interactions
            ],
        )
