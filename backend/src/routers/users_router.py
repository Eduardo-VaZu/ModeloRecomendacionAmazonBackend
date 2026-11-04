"""Endpoints de usuarios: búsqueda, historial, recomendaciones y recorrido del híbrido."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..persistency.database.models import RecommenderModel
from ..use_cases.users import (
    DemoUserPageResponse,
    GetUserHistoryHandler,
    GetUserHistoryRequest,
    GetUserPipelineHandler,
    GetUserPipelineRequest,
    GetUserRecommendationsHandler,
    GetUserRecommendationsRequest,
    ListDemoUsersHandler,
    ListDemoUsersRequest,
    UserHistoryResponse,
    UserPipelineResponse,
    UserRecommendationsResponse,
)

users_router = APIRouter(prefix="/users", tags=["users"])

TopK = Annotated[int, Query(ge=1, le=20)]


@users_router.get("", response_model=DemoUserPageResponse)
async def list_users(
    handler: Annotated[ListDemoUsersHandler, Depends()],
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DemoUserPageResponse:
    """Usuarios de la muestra, filtrables por id."""
    return await handler.execute(ListDemoUsersRequest(search=search, limit=limit, offset=offset))


@users_router.get("/{user_id}/history", response_model=UserHistoryResponse)
async def get_history(
    user_id: str, handler: Annotated[GetUserHistoryHandler, Depends()]
) -> UserHistoryResponse:
    """Historial cronológico del usuario con su partición temporal."""
    return await handler.execute(GetUserHistoryRequest(user_id=user_id))


@users_router.get("/{user_id}/recommendations", response_model=UserRecommendationsResponse)
async def get_recommendations(
    user_id: str,
    handler: Annotated[GetUserRecommendationsHandler, Depends()],
    model: RecommenderModel = RecommenderModel.HYBRID,
    k: TopK = 10,
) -> UserRecommendationsResponse:
    """Top-K del modelo indicado para el usuario."""
    return await handler.execute(GetUserRecommendationsRequest(user_id=user_id, model=model, k=k))


@users_router.get("/{user_id}/pipeline", response_model=UserPipelineResponse)
async def get_pipeline(
    user_id: str, handler: Annotated[GetUserPipelineHandler, Depends()], k: TopK = 10
) -> UserPipelineResponse:
    """Candidatos de la Etapa 1 y su reordenamiento en la Etapa 2."""
    return await handler.execute(GetUserPipelineRequest(user_id=user_id, k=k))
