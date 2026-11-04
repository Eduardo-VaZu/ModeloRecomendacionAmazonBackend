"""Modelos O1 y contrato común de `Recommender` (incluye R10: tiempo de entrenamiento)."""

import numpy as np
import pytest

from recsys.config import EvaluationConfig
from recsys.evaluation.evaluator import evaluate
from recsys.models.baselines import ItemMeanRecommender, PopularityRecommender


def test_popularity_ranks_by_count_and_excludes_seen(train_data):
    model = PopularityRecommender().fit(train_data)

    # El usuario 2 ya vio el producto 0 (el más popular).
    assert set(model.recommend(np.array([2]), k=2)[0].tolist()) == {1, 2}
    assert model.predict_rating(np.array([0]), np.array([3])) == pytest.approx([4.2])


def test_fit_records_training_time(train_data):
    for model in (PopularityRecommender(), ItemMeanRecommender()):
        assert model.fit(train_data).train_time_s >= 0


def test_recommend_before_fit_fails():
    with pytest.raises(RuntimeError):
        PopularityRecommender().recommend(np.array([0]), k=1)


def test_evaluate_reports_every_thesis_metric(train_data):
    config = EvaluationConfig(k_values=(1, 2), relevance_threshold=4.0, batch_size=2)
    model = ItemMeanRecommender().fit(train_data)

    results = evaluate(model, train_data, config)

    expected = {"rmse", "mae", "train_time_s"} | {
        f"{metric}@{k}" for metric in ("precision", "recall", "f1", "coverage") for k in (1, 2)
    }
    assert expected <= results.keys()
