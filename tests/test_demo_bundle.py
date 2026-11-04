import json

import pandas as pd
import pytest

from recsys.export.demo_bundle import DatasetSummary, DemoBundle, results_to_long


def _summary() -> DatasetSummary:
    return DatasetSummary("src", "cat", False, 1, 1, 1, 10)


def test_results_to_long_splits_metric_and_k():
    wide = pd.DataFrame({"model": ["hybrid"], "rmse": [0.9], "precision@10": [0.03]})
    long = results_to_long(wide).set_index("metric")

    assert long.loc["rmse", "value"] == pytest.approx(0.9)
    assert pd.isna(long.loc["rmse", "k"])
    assert long.loc["precision", "k"] == 10


def test_bundle_rejects_missing_columns(tmp_path):
    empty = pd.DataFrame()
    bundle = DemoBundle(_summary(), empty, empty, empty, empty, empty)

    with pytest.raises(ValueError, match="products"):
        bundle.write(tmp_path)


def test_bundle_writes_every_table(tmp_path):
    def frame(*columns: str) -> pd.DataFrame:
        return pd.DataFrame({column: [] for column in columns})

    bundle = DemoBundle(
        _summary(),
        frame("product_id", "title", "category", "store"),
        frame("user_id", "n_interactions"),
        frame("user_id", "product_id", "rating", "timestamp", "split"),
        frame("user_id", "model", "rank", "product_id", "content_score", "als_score",
              "final_score", "is_hit", "reason_product_id"),
        frame("model", "metric", "k", "value"),
    )
    bundle.write(tmp_path)

    written = {path.name for path in tmp_path.iterdir()}
    assert {"summary.json", "products.jsonl", "recommendations.jsonl"} <= written
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["n_candidates"] == 10
