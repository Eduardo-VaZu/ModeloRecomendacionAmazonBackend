"""Paquete de datos que consume el prototipo visual (`backend/src/seed.py`).

Contrato entre el pipeline y el backend: un `.jsonl` por tabla y un `summary.json`. El backend
no conoce pandas ni los modelos; solo importa estos archivos a Postgres.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PRODUCT_COLUMNS = ["product_id", "title", "category", "store"]
USER_COLUMNS = ["user_id", "n_interactions"]
INTERACTION_COLUMNS = ["user_id", "product_id", "rating", "timestamp", "split"]
RECOMMENDATION_COLUMNS = [
    "user_id",
    "model",
    "rank",
    "product_id",
    "content_score",
    "als_score",
    "final_score",
    "is_hit",
    "reason_product_id",
]
RESULT_COLUMNS = ["model", "metric", "k", "value"]

_TABLES = {
    "products": PRODUCT_COLUMNS,
    "users": USER_COLUMNS,
    "interactions": INTERACTION_COLUMNS,
    "recommendations": RECOMMENDATION_COLUMNS,
    "experiment_results": RESULT_COLUMNS,
}


@dataclass(frozen=True)
class DatasetSummary:
    source: str
    category: str
    is_synthetic: bool
    n_users: int
    n_items: int
    n_interactions: int
    n_candidates: int


@dataclass(frozen=True)
class DemoBundle:
    summary: DatasetSummary
    products: pd.DataFrame
    users: pd.DataFrame
    interactions: pd.DataFrame
    recommendations: pd.DataFrame
    experiment_results: pd.DataFrame

    def write(self, directory: Path) -> None:
        """Valida las columnas de cada tabla y escribe el paquete en `directory`."""
        directory.mkdir(parents=True, exist_ok=True)
        for name, columns in _TABLES.items():
            frame: pd.DataFrame = getattr(self, name)
            missing = set(columns) - set(frame.columns)
            if missing:
                raise ValueError(f"A la tabla '{name}' le faltan columnas: {sorted(missing)}")
            frame[columns].to_json(
                directory / f"{name}.jsonl", orient="records", lines=True, force_ascii=False
            )
        summary = json.dumps(self.summary.__dict__, indent=2, ensure_ascii=False)
        (directory / "summary.json").write_text(summary, encoding="utf-8")


def results_to_long(results: pd.DataFrame) -> pd.DataFrame:
    """Convierte la tabla ancha de `05_evaluate` (una columna por métrica) a filas
    (modelo, métrica, k, valor); por ejemplo `precision@10` → (`precision`, 10)."""
    long = results.melt(id_vars="model", var_name="column", value_name="value")
    parts = long["column"].str.split("@", n=1, expand=True)
    k = parts[1] if parts.shape[1] > 1 else pd.Series(None, index=long.index)
    return pd.DataFrame(
        {
            "model": long["model"],
            "metric": parts[0],
            "k": pd.to_numeric(k).astype("Int64"),
            "value": long["value"].astype(float),
        }
    )
