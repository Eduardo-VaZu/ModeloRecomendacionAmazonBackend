"""Modelos no personalizados: mediciones O1 (pre-test) del diseño pre-experimental."""

from __future__ import annotations

import numpy as np

from recsys.data.dataset import InteractionData
from recsys.models.base import Recommender
from recsys.schema import ITEM_IDX, RATING


class PopularityRecommender(Recommender):
    """Recomienda los productos con más interacciones; predice la media global de ratings."""

    name = "popularity"

    def _fit(self, train: InteractionData) -> None:
        frame = train.frame
        self._popularity = np.bincount(frame[ITEM_IDX], minlength=train.n_items).astype(np.float32)
        self._global_mean = float(frame[RATING].mean())

    def _score_items(self, user_idx: np.ndarray) -> np.ndarray:
        return np.broadcast_to(self._popularity, (len(user_idx), len(self._popularity)))

    def predict_rating(self, user_idx: np.ndarray, item_idx: np.ndarray) -> np.ndarray:
        return np.full(len(item_idx), self._global_mean)


class ItemMeanRecommender(Recommender):
    """Recomienda y predice con la media de rating de cada producto.

    La media se suaviza hacia la media global con `damping` interacciones ficticias para que
    productos con pocas reseñas no dominen el ranking.
    """

    name = "item_mean"

    def __init__(self, damping: float = 5.0) -> None:
        super().__init__()
        self.damping = damping

    def _fit(self, train: InteractionData) -> None:
        frame = train.frame
        global_mean = frame[RATING].mean()
        sums = np.bincount(frame[ITEM_IDX], weights=frame[RATING], minlength=train.n_items)
        counts = np.bincount(frame[ITEM_IDX], minlength=train.n_items)
        self._item_mean = (sums + self.damping * global_mean) / (counts + self.damping)

    def _score_items(self, user_idx: np.ndarray) -> np.ndarray:
        return np.broadcast_to(self._item_mean, (len(user_idx), len(self._item_mean)))

    def predict_rating(self, user_idx: np.ndarray, item_idx: np.ndarray) -> np.ndarray:
        return self._item_mean[np.asarray(item_idx)]
