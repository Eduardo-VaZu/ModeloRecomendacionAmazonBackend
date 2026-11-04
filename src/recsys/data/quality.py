"""R13: reglas de calidad de datos (duplicados y completitud)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from recsys.schema import ITEM_ID, RATING, TIMESTAMP, USER_ID

REQUIRED_REVIEW_FIELDS = [USER_ID, ITEM_ID, RATING, TIMESTAMP]


def _is_filled(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and np.isnan(value):
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, np.ndarray)):
        return len(value) > 0
    return True


def completeness(frame: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
    """Proporción de campos con contenido (no nulos ni vacíos) por registro."""
    return frame[list(columns)].map(_is_filled).mean(axis=1)


def filter_by_completeness(
    frame: pd.DataFrame, columns: Sequence[str], min_ratio: float
) -> pd.DataFrame:
    return frame[completeness(frame, columns) >= min_ratio]


def drop_duplicate_interactions(reviews: pd.DataFrame) -> pd.DataFrame:
    """Conserva solo la reseña más reciente de cada par (usuario, producto)."""
    return reviews.sort_values(TIMESTAMP, kind="stable").drop_duplicates(
        [USER_ID, ITEM_ID], keep="last"
    )


def apply_quality_rules(
    reviews: pd.DataFrame,
    meta: pd.DataFrame,
    meta_fields: Sequence[str],
    min_completeness: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Aplica las reglas de calidad y devuelve cuántos registros eliminó cada una."""
    report: dict[str, int] = {}

    complete_reviews = filter_by_completeness(reviews, REQUIRED_REVIEW_FIELDS, 1.0)
    report["reviews_incomplete"] = len(reviews) - len(complete_reviews)

    unique_reviews = drop_duplicate_interactions(complete_reviews)
    report["reviews_duplicated"] = len(complete_reviews) - len(unique_reviews)

    unique_meta = meta.drop_duplicates(ITEM_ID, keep="first")
    report["meta_duplicated"] = len(meta) - len(unique_meta)

    complete_meta = filter_by_completeness(unique_meta, meta_fields, min_completeness)
    report["meta_incomplete"] = len(unique_meta) - len(complete_meta)

    kept_reviews = unique_reviews[unique_reviews[ITEM_ID].isin(complete_meta[ITEM_ID])]
    report["reviews_without_valid_meta"] = len(unique_reviews) - len(kept_reviews)

    return kept_reviews.reset_index(drop=True), complete_meta.reset_index(drop=True), report
