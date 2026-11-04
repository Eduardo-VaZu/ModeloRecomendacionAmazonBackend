"""Partición temporal por usuario en train / validación / test."""

from __future__ import annotations

import numpy as np
import pandas as pd

from recsys.schema import TIMESTAMP, USER_IDX


def temporal_user_split(
    interactions: pd.DataFrame, val_ratio: float, test_ratio: float, user_col: str = USER_IDX
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Envía las interacciones más recientes de cada usuario a test y las anteriores a validación.

    Cada usuario aporta al menos una interacción a validación y otra a test, de modo que nunca
    se usa información del futuro para predecir el pasado.
    """
    frame = interactions.sort_values([user_col, TIMESTAMP], kind="stable")
    groups = frame.groupby(user_col)
    position_from_end = groups.cumcount(ascending=False).to_numpy()
    sizes = groups[user_col].transform("size").to_numpy()

    n_test = np.maximum(1, np.floor(sizes * test_ratio)).astype(int)
    n_val = np.maximum(1, np.floor(sizes * val_ratio)).astype(int)

    is_test = position_from_end < n_test
    is_val = ~is_test & (position_from_end < n_test + n_val)
    is_train = ~(is_test | is_val)

    return (
        frame[is_train].reset_index(drop=True),
        frame[is_val].reset_index(drop=True),
        frame[is_test].reset_index(drop=True),
    )
