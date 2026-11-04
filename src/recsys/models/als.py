"""R4 - Etapa 2: factorización de matrices con ALS de la librería `implicit` (Fase 4).

Plan: matriz de confianza c = 1 + alpha * w(rating, verified_purchase, helpful_vote), que combina
la señal explícita (rating) con la implícita (que la interacción exista).
`implicit >= 0.7` espera la matriz usuarios × productos en `fit()`.
"""

from __future__ import annotations

import numpy as np

from recsys.config import ALSConfig
from recsys.data.dataset import InteractionData
from recsys.models.base import Recommender


class ALSRecommender(Recommender):
    name = "als"

    def __init__(self, config: ALSConfig, seed: int) -> None:
        super().__init__()
        self.config = config
        self.seed = seed

    def _fit(self, train: InteractionData) -> None:
        raise NotImplementedError("Fase 4: ALS")

    def _score_items(self, user_idx: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Fase 4: ALS")

    def predict_rating(self, user_idx: np.ndarray, item_idx: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Fase 4: ALS")
