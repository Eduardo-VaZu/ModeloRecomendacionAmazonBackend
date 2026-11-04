"""Protocolo único de evaluación: el mismo para O1 (baselines) y O2 (híbrido)."""

from __future__ import annotations

import numpy as np

from recsys.config import EvaluationConfig
from recsys.data.dataset import InteractionData
from recsys.evaluation.coverage import catalog_coverage
from recsys.evaluation.ranking_metrics import ranking_scores_at_k
from recsys.evaluation.rating_metrics import mae, rmse
from recsys.models.base import Recommender
from recsys.schema import ITEM_IDX, RATING, USER_IDX


def evaluate(
    model: Recommender, test: InteractionData, config: EvaluationConfig
) -> dict[str, float | str]:
    """Calcula RMSE, MAE, Precision/Recall/F1@K, cobertura y tiempo de entrenamiento.

    Un producto de test es relevante si su rating >= `relevance_threshold`.
    """
    frame = test.frame
    predictions = model.predict_rating(frame[USER_IDX].to_numpy(), frame[ITEM_IDX].to_numpy())
    results: dict[str, float | str] = {
        "model": model.name,
        "rmse": rmse(frame[RATING].to_numpy(), predictions),
        "mae": mae(frame[RATING].to_numpy(), predictions),
    }

    relevant = (
        frame[frame[RATING] >= config.relevance_threshold].groupby(USER_IDX)[ITEM_IDX].agg(set)
    )
    users = relevant.index.to_numpy()
    recommended = _recommend_in_batches(model, users, max(config.k_values), config.batch_size)

    for k in config.k_values:
        scores = ranking_scores_at_k(recommended, relevant.to_list(), k)
        results[f"precision@{k}"] = scores.precision
        results[f"recall@{k}"] = scores.recall
        results[f"f1@{k}"] = scores.f1
        results[f"coverage@{k}"] = catalog_coverage(recommended[:, :k], test.n_items)

    results["train_time_s"] = model.train_time_s if model.train_time_s is not None else np.nan
    return results


def _recommend_in_batches(
    model: Recommender, users: np.ndarray, k: int, batch_size: int
) -> np.ndarray:
    if len(users) == 0:
        return np.empty((0, k), dtype=int)
    batches = [
        model.recommend(users[start : start + batch_size], k)
        for start in range(0, len(users), batch_size)
    ]
    return np.vstack(batches)
