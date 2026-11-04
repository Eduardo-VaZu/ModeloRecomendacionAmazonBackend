"""Peticiones de los casos de uso de usuarios."""

from __future__ import annotations

from ...persistency.database.models import RecommenderModel
from ..shared.base_data_transfer import BaseDataTransfer


class ListDemoUsersRequest(BaseDataTransfer):
    """Página de usuarios, opcionalmente filtrada por id."""

    search: str | None = None
    limit: int = 20
    offset: int = 0


class GetUserHistoryRequest(BaseDataTransfer):
    """Historial de un usuario."""

    user_id: str


class GetUserRecommendationsRequest(BaseDataTransfer):
    """Top-K de un modelo para un usuario."""

    user_id: str
    model: RecommenderModel
    k: int = 10


class GetUserPipelineRequest(BaseDataTransfer):
    """Recorrido por las dos etapas del híbrido para un usuario."""

    user_id: str
    k: int = 10
