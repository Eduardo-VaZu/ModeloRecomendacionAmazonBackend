"""R13: duplicados y completitud mínima."""

import numpy as np
import pandas as pd

from recsys.data.quality import apply_quality_rules, completeness, drop_duplicate_interactions
from recsys.schema import ITEM_ID, RATING, TIMESTAMP, USER_ID

META_FIELDS = ["title", "features", "description", "categories", "store"]


def test_duplicates_keep_most_recent_review():
    reviews = pd.DataFrame(
        {USER_ID: ["u", "u"], ITEM_ID: ["i", "i"], RATING: [1.0, 5.0], TIMESTAMP: [1, 2]}
    )
    result = drop_duplicate_interactions(reviews)

    assert len(result) == 1
    assert result[RATING].item() == 5.0


def test_completeness_treats_empty_values_as_missing():
    meta = pd.DataFrame(
        {
            "title": ["A", "B"],
            "features": [["f"], []],
            "description": [["d"], None],
            "categories": [["c"], [""]],
            "store": ["s", "   "],
        }
    )
    assert completeness(meta, META_FIELDS).tolist() == [1.0, 0.4]


def test_quality_rules_report_every_removal():
    reviews = pd.DataFrame(
        {
            USER_ID: ["u1", "u1", "u2", "u3"],
            ITEM_ID: ["good", "good", "bad", "good"],
            RATING: [4.0, 5.0, 3.0, np.nan],
            TIMESTAMP: [1, 2, 3, 4],
        }
    )
    meta = pd.DataFrame(
        {
            ITEM_ID: ["good", "bad"],
            "title": ["t", "t"],
            "features": [["f"], []],
            "description": [["d"], []],
            "categories": [["c"], []],
            "store": ["s", "s"],
        }
    )
    kept_reviews, kept_meta, report = apply_quality_rules(reviews, meta, META_FIELDS, 0.9)

    assert report == {
        "reviews_incomplete": 1,
        "reviews_duplicated": 1,
        "meta_duplicated": 0,
        "meta_incomplete": 1,
        "reviews_without_valid_meta": 1,
    }
    assert kept_reviews[ITEM_ID].tolist() == ["good"]
    assert kept_meta[ITEM_ID].tolist() == ["good"]
