"""R7, R8 y R9: métricas verificadas con valores calculados a mano."""

import numpy as np
import pandas as pd
import pytest

from recsys.evaluation.coverage import catalog_coverage
from recsys.evaluation.ranking_metrics import ranking_scores_at_k
from recsys.evaluation.rating_metrics import mae, rmse
from recsys.experiments.pre_post import pre_post_table


def test_rmse_and_mae():
    y_true = np.array([5.0, 3.0, 4.0])
    y_pred = np.array([4.0, 3.0, 2.0])

    assert rmse(y_true, y_pred) == pytest.approx(np.sqrt(5 / 3))
    assert mae(y_true, y_pred) == pytest.approx(1.0)


def test_precision_recall_f1_at_k():
    recommended = np.array([[1, 2, 3], [4, 5, 6]])
    relevant = [{1, 9}, {7}]

    scores = ranking_scores_at_k(recommended, relevant, k=2)

    # Usuario 0: 1 acierto de 2 → P=0.5, R=0.5. Usuario 1: 0 aciertos.
    assert scores.precision == pytest.approx(0.25)
    assert scores.recall == pytest.approx(0.25)
    assert scores.f1 == pytest.approx(0.25)


def test_catalog_coverage():
    assert catalog_coverage(np.array([[0, 1], [1, 2]]), n_items=6) == pytest.approx(0.5)


def test_pre_post_table_marks_direction_of_improvement():
    table = pre_post_table(
        {"model": "popularity", "rmse": 1.2, "precision@10": 0.02},
        {"model": "hybrid", "rmse": 1.0, "precision@10": 0.05},
    ).set_index("metric")

    assert isinstance(table, pd.DataFrame)
    assert "model" not in table.index
    assert table.loc["rmse", "improved"]
    assert table.loc["precision@10", "improved"]
