"""Caso de uso: Top-K de un modelo para un usuario."""

from __future__ import annotations

from itertools import chain

from ..shared.base_handler import BaseHandler
from .ensure_user_exists import ensure_user_exists
from .user_requests import GetUserRecommendationsRequest
from .user_responses import RecommendationItemResponse, UserRecommendationsResponse


class GetUserRecommendationsHandler(
    BaseHandler[GetUserRecommendationsRequest, UserRecommendationsResponse]
):
    """Devuelve las recomendaciones precalculadas de un modelo."""

    async def execute(self, request: GetUserRecommendationsRequest) -> UserRecommendationsResponse:
        await ensure_user_exists(self._unit_of_work, request.user_id)
        recommendations = await self._unit_of_work.recommendations.get_top_k(
            request.user_id, request.model, request.k
        )
        product_ids = chain.from_iterable(
            (r.product_id, r.reason_product_id or "") for r in recommendations
        )
        products = await self._unit_of_work.products.get_map(product_ids)
        return UserRecommendationsResponse(
            user_id=request.user_id,
            model=request.model,
            items=[RecommendationItemResponse.build(r, products) for r in recommendations],
        )
