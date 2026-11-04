"""R2: solo deben quedar usuarios y productos con al menos 5 interacciones."""

import pandas as pd
import pytest

from recsys.config import FilteringConfig
from recsys.data.preprocessing import encode_ids, k_core_filter
from recsys.schema import ITEM_ID, ITEM_IDX, USER_ID, USER_IDX


def test_kcore_keeps_only_active_users_and_items(raw_reviews):
    filtered = k_core_filter(raw_reviews, k=5)

    assert filtered[USER_ID].value_counts().min() >= 5
    assert filtered[ITEM_ID].value_counts().min() >= 5
    assert "u_inactive" not in set(filtered[USER_ID])
    assert "i_rare" not in set(filtered[ITEM_ID])


def test_kcore_is_iterative():
    # Quitar u_c deja a i_c con 1 interacción; quitar i_c deja a u_d con 1: efecto en cadena.
    frame = pd.DataFrame(
        {
            USER_ID: ["u_a", "u_a", "u_b", "u_b", "u_c", "u_d", "u_d"],
            ITEM_ID: ["i_a", "i_b", "i_a", "i_b", "i_c", "i_c", "i_a"],
        }
    )
    filtered = k_core_filter(frame, k=2)

    assert set(filtered[USER_ID]) == {"u_a", "u_b"}
    assert set(filtered[ITEM_ID]) == {"i_a", "i_b"}


def test_config_rejects_k_core_below_thesis_minimum():
    with pytest.raises(ValueError):
        FilteringConfig(k_core=4)


def test_encode_ids_is_consecutive(raw_reviews):
    encoded, users, items = encode_ids(k_core_filter(raw_reviews, k=5))

    assert sorted(encoded[USER_IDX].unique()) == list(range(len(users)))
    assert sorted(encoded[ITEM_IDX].unique()) == list(range(len(items)))
