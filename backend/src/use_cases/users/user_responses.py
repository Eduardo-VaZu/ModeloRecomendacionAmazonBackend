"""Respuestas de los casos de uso de usuarios."""

from __future__ import annotations

from datetime import datetime

from ...persistency.database.models import DataSplit, Product, Recommendation, RecommenderModel
from ..shared.base_data_transfer import BaseDataTransfer


class ProductResponse(BaseDataTransfer):
    """Datos visibles de un producto."""

    product_id: str
    title: str
    category: str
    store: str | None

    @classmethod
    def from_map(cls, products: dict[str, Product], product_id: str) -> ProductResponse:
        """Producto del mapa, o un marcador si no está en el catálogo exportado."""
        product = products.get(product_id)
        if product is None:
            return cls(product_id=product_id, title=product_id, category="", store=None)
        return cls.model_validate(product)


class DemoUserResponse(BaseDataTransfer):
    """Usuario de la muestra."""

    user_id: str
    n_interactions: int


class DemoUserPageResponse(BaseDataTransfer):
    """Página de usuarios con el total de coincidencias."""

    items: list[DemoUserResponse]
    total: int


class InteractionResponse(BaseDataTransfer):
    """Reseña del historial con su partición temporal."""

    product: ProductResponse
    rating: float
    reviewed_at: datetime
    split: DataSplit


class UserHistoryResponse(BaseDataTransfer):
    """Historial cronológico de un usuario."""

    user_id: str
    interactions: list[InteractionResponse]


class RecommendationItemResponse(BaseDataTransfer):
    """Producto recomendado con sus puntajes por etapa."""

    rank: int
    product: ProductResponse
    content_score: float | None
    als_score: float | None
    final_score: float
    is_hit: bool
    reason_product: ProductResponse | None

    @classmethod
    def build(
        cls, recommendation: Recommendation, products: dict[str, Product]
    ) -> RecommendationItemResponse:
        """Combina la recomendación con los datos de sus productos."""
        reason_id = recommendation.reason_product_id
        return cls(
            rank=recommendation.rank,
            product=ProductResponse.from_map(products, recommendation.product_id),
            content_score=recommendation.content_score,
            als_score=recommendation.als_score,
            final_score=recommendation.final_score,
            is_hit=recommendation.is_hit,
            reason_product=ProductResponse.from_map(products, reason_id) if reason_id else None,
        )


class UserRecommendationsResponse(BaseDataTransfer):
    """Top-K de un modelo para un usuario."""

    user_id: str
    model: RecommenderModel
    items: list[RecommendationItemResponse]


class PipelineItemResponse(RecommendationItemResponse):
    """Recomendación final con la posición que tenía entre los candidatos de la Etapa 1."""

    candidate_rank: int | None


class UserPipelineResponse(BaseDataTransfer):
    """Etapa 1 (candidatos por contenido) y Etapa 2 (reordenamiento con ALS)."""

    user_id: str
    n_candidates: int
    candidates: list[RecommendationItemResponse]
    final: list[PipelineItemResponse]
