"""R2: filtrado de perfiles activos (k-core) y codificación de identificadores."""

from __future__ import annotations

import pandas as pd

from recsys.schema import ITEM_ID, ITEM_IDX, USER_ID, USER_IDX


def k_core_filter(
    interactions: pd.DataFrame, k: int, user_col: str = USER_ID, item_col: str = ITEM_ID
) -> pd.DataFrame:
    """Elimina usuarios y productos con menos de `k` interacciones hasta que no quede ninguno.

    Es iterativo porque quitar productos puede dejar a un usuario por debajo de `k` y viceversa.
    """
    frame = interactions
    while True:
        user_counts = frame[user_col].map(frame[user_col].value_counts())
        item_counts = frame[item_col].map(frame[item_col].value_counts())
        keep = (user_counts >= k) & (item_counts >= k)
        if keep.all():
            return frame.reset_index(drop=True)
        frame = frame[keep]


def encode_ids(interactions: pd.DataFrame) -> tuple[pd.DataFrame, pd.Index, pd.Index]:
    """Asigna índices enteros consecutivos a usuarios y productos.

    Devuelve las interacciones con `USER_IDX`/`ITEM_IDX` y los índices para revertir el mapeo.
    """
    user_codes, users = pd.factorize(interactions[USER_ID], sort=True)
    item_codes, items = pd.factorize(interactions[ITEM_ID], sort=True)
    encoded = interactions.assign(**{USER_IDX: user_codes, ITEM_IDX: item_codes})
    return encoded, pd.Index(users, name=USER_ID), pd.Index(items, name=ITEM_ID)
