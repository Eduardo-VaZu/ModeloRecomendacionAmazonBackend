"""Caso de uso: recorrido por las dos etapas del modelo híbrido."""

from __future__ import annotations

from itertools import chain

from ...persistency.database.models import RecommenderModel
from ..shared.base_handler import BaseHandler
from .ensure_user_exists import ensure_user_exists
from .user_requests import GetUserPipelineRequest
from .user_responses import (
    PipelineItemResponse,
    RecommendationItemResponse,
    UserPipelineResponse,
)

CANDIDATES_SHOWN = 20


class GetUserPipelineHandler(BaseHandler[GetUserPipelineRequest, UserPipelineResponse]):
    """Muestra los candidatos de contenido y cómo ALS los reordena en el Top-K final."""

    async def execute(self, request: GetUserPipelineRequest) -> UserPipelineResponse:
        await ensure_user_exists(self._unit_of_work, request.user_id)
        repository = self._unit_of_work.recommendations
        candidates = await repository.get_top_k(
            request.user_id, RecommenderModel.CONTENT_BASED, CANDIDATES_SHOWN
        )
        final = await repository.get_top_k(request.user_id, RecommenderModel.HYBRID, request.k)
        summary = await self._unit_of_work.dataset_summaries.get_current()

        product_ids = chain.from_iterable(
            (r.product_id, r.reason_product_id or "") for r in (*candidates, *final)
        )
        products = await self._unit_of_work.products.get_map(product_ids)
        candidate_rank = {c.product_id: c.rank for c in candidates}

        return UserPipelineResponse(
            user_id=request.user_id,
            n_candidates=summary.n_candidates if summary else len(candidates),
            candidates=[RecommendationItemResponse.build(c, products) for c in candidates],
            final=[
                PipelineItemResponse(
                    **RecommendationItemResponse.build(r, products).model_dump(),
                    candidate_rank=candidate_rank.get(r.product_id),
                )
                for r in final
            ],
        )
