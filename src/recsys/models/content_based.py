"""R3 - Etapa 1: filtrado basado en contenido (Fase 3).

Plan: perfil de usuario = promedio de los vectores TF-IDF de sus productos ponderado por rating;
puntaje = similitud coseno del perfil contra todo el catálogo.
"""

from __future__ import annotations

import numpy as np

from recsys.config import ContentConfig
from recsys.data.dataset import InteractionData
from recsys.models.base import Recommender


class ContentBasedRecommender(Recommender):
    name = "content_based"

    def __init__(self, config: ContentConfig) -> None:
        super().__init__()
        self.config = config

    def _fit(self, train: InteractionData) -> None:
        raise NotImplementedError("Fase 3: filtrado basado en contenido")

    def _score_items(self, user_idx: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Fase 3: filtrado basado en contenido")

    def predict_rating(self, user_idx: np.ndarray, item_idx: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Fase 3: filtrado basado en contenido")
