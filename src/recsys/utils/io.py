"""Lectura y escritura de tablas y modelos."""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


def save_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def save_object(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, path)


def load_object(path: Path) -> Any:
    return joblib.load(path)
