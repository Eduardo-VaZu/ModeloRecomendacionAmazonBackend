"""Interfaz común: todos los modelos se entrenan y evalúan igual."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import scipy.sparse as sp

from recsys.data.dataset import InteractionData
from recsys.utils.timing import Timer


def top_k(scores: np.ndarray, k: int, seen: sp.csr_matrix | None = None) -> np.ndarray:
    """Índices de los `k` productos con mayor puntaje por fila, ordenados de mayor a menor."""
    scores = np.array(scores, dtype=np.float32)
    if seen is not None:
        rows, cols = seen.nonzero()
        scores[rows, cols] = -np.inf
    k = min(k, scores.shape[1])
    candidates = np.argpartition(-scores, kth=k - 1, axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(scores, candidates, axis=1), axis=1, kind="stable")
    return np.take_along_axis(candidates, order, axis=1)


class Recommender(ABC):
    """Contrato de los modelos (baselines, contenido, ALS e híbrido).

    `fit` mide el tiempo de entrenamiento en segundos (R10) y guarda los productos ya vistos
    para no volver a recomendarlos.
    """

    name: str = "recommender"

    def __init__(self) -> None:
        self.train_time_s: float | None = None
        self._seen: sp.csr_matrix | None = None

    def fit(self, train: InteractionData) -> Recommender:
        self._seen = train.to_csr()
        with Timer() as timer:
            self._fit(train)
        self.train_time_s = timer.seconds
        return self

    def recommend(self, user_idx: np.ndarray, k: int, exclude_seen: bool = True) -> np.ndarray:
        """Matriz (n_usuarios, k) con los índices de producto recomendados."""
        if self._seen is None:
            raise RuntimeError(f"{self.name} no está entrenado; llama a fit() primero")
        user_idx = np.asarray(user_idx)
        seen = self._seen[user_idx] if exclude_seen else None
        return top_k(self._score_items(user_idx), k, seen)

    @abstractmethod
    def _fit(self, train: InteractionData) -> None: ...

    @abstractmethod
    def _score_items(self, user_idx: np.ndarray) -> np.ndarray:
        """Puntaje de cada producto del catálogo para cada usuario: (n_usuarios, n_productos)."""

    @abstractmethod
    def predict_rating(self, user_idx: np.ndarray, item_idx: np.ndarray) -> np.ndarray:
        """Rating estimado (escala 1-5) para cada par (usuario, producto); usado en RMSE/MAE."""
