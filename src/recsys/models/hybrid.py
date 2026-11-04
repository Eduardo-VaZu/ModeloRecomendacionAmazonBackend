"""R5: modelo híbrido en dos etapas, medición O2 (post-test) (Fase 5).

Etapa 1: `ContentBasedRecommender` genera `n_candidates` productos por usuario.
Etapa 2: `ALSRecommender` puntúa esos candidatos; el puntaje final es
`blend_weight * ALS + (1 - blend_weight) * contenido` (ambos normalizados).
Los productos fuera de los candidatos reciben -inf y nunca se recomiendan.
"""

from __future__ import annotations

import numpy as np

from recsys.config import HybridConfig
from recsys.data.dataset import InteractionData
from recsys.models.als import ALSRecommender
from recsys.models.base import Recommender
from recsys.models.content_based import ContentBasedRecommender


class HybridRecommender(Recommender):
    name = "hybrid"

    def __init__(
        self, content: ContentBasedRecommender, als: ALSRecommender, config: HybridConfig
    ) -> None:
        super().__init__()
        self.content = content
        self.als = als
        self.config = config

    def _fit(self, train: InteractionData) -> None:
        raise NotImplementedError("Fase 5: modelo híbrido")

    def _score_items(self, user_idx: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Fase 5: modelo híbrido")

    def predict_rating(self, user_idx: np.ndarray, item_idx: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Fase 5: modelo híbrido")
