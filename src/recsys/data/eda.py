"""Análisis exploratorio de datos (CRISP-DM, Fase 02: comprensión de los datos).

Funciones puras sobre tablas de interacciones; `scripts/08_eda.py` las aplica al dataset real.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from recsys.schema import ITEM_ID, RATING, TIMESTAMP, USER_ID


def funnel_table(stages: Sequence[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    """Reseñas, usuarios e ítems que quedan después de cada paso de la preparación."""
    rows = [
        {
            "stage": name,
            "reviews": len(frame),
            "users": frame[USER_ID].nunique(),
            "items": frame[ITEM_ID].nunique(),
        }
        for name, frame in stages
    ]
    table = pd.DataFrame(rows)
    table["pct_of_previous"] = table["reviews"] / table["reviews"].shift(1) * 100
    return table


def rating_distribution(interactions: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Cantidad y porcentaje de cada calificación (1-5) y si cuenta como relevante."""
    counts = interactions[RATING].value_counts().sort_index()
    return pd.DataFrame(
        {
            "rating": counts.index.astype(float),
            "n": counts.to_numpy(),
            "pct": counts.to_numpy() / counts.sum() * 100,
            "relevant": counts.index >= threshold,
        }
    )


def monthly_counts(interactions: pd.DataFrame) -> pd.DataFrame:
    """Interacciones por mes (UTC), a partir de `timestamp` en milisegundos."""
    months = pd.to_datetime(interactions[TIMESTAMP], unit="ms", utc=True).dt.strftime("%Y-%m")
    counts = months.value_counts().sort_index()
    return pd.DataFrame({"month": counts.index, "n": counts.to_numpy()})


def long_tail_stats(interactions: pd.DataFrame) -> dict[str, float]:
    """Concentración de la actividad: interacciones por usuario y por ítem (cola larga)."""
    per_user = interactions[USER_ID].value_counts()
    per_item = interactions[ITEM_ID].value_counts()  # ordenado de mayor a menor
    total = per_item.sum()
    top_1 = max(1, int(np.ceil(len(per_item) * 0.01)))
    top_10 = max(1, int(np.ceil(len(per_item) * 0.10)))
    return {
        "user_interactions_min": int(per_user.min()),
        "user_interactions_median": float(per_user.median()),
        "user_interactions_mean": float(per_user.mean()),
        "user_interactions_max": int(per_user.max()),
        "item_interactions_median": float(per_item.median()),
        "item_interactions_mean": float(per_item.mean()),
        "item_interactions_max": int(per_item.max()),
        "pct_items_single_interaction": float((per_item == 1).mean() * 100),
        "pct_interactions_top_1pct_items": float(per_item.iloc[:top_1].sum() / total * 100),
        "pct_interactions_top_10pct_items": float(per_item.iloc[:top_10].sum() / total * 100),
    }
