"""R8: exactitud del ranking (Precision@K, Recall@K, F1@K)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RankingScores:
    precision: float
    recall: float
    f1: float


def ranking_scores_at_k(
    recommended: np.ndarray, relevant: Sequence[set[int]], k: int
) -> RankingScores:
    """Promedia Precision@K y Recall@K entre usuarios; F1@K es su media armónica.

    `recommended[u]` son los productos recomendados al usuario u (al menos `k`) y `relevant[u]`
    sus productos relevantes en test. Solo deben incluirse usuarios con algún relevante.
    """
    if len(relevant) == 0:
        return RankingScores(0.0, 0.0, 0.0)
    pairs = zip(recommended, relevant, strict=True)
    hits = np.array([len(set(items[:k].tolist()) & rel) for items, rel in pairs])
    n_relevant = np.array([len(rel) for rel in relevant])
    precision = float(np.mean(hits / k))
    recall = float(np.mean(hits / n_relevant))
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return RankingScores(precision, recall, f1)
