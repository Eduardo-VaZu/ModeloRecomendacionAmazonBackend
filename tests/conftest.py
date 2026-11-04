import numpy as np
import pandas as pd
import pytest

from recsys.data.dataset import InteractionData
from recsys.schema import ITEM_ID, ITEM_IDX, RATING, TIMESTAMP, USER_ID, USER_IDX


@pytest.fixture
def raw_reviews() -> pd.DataFrame:
    """Usuarios u0-u5 con 6 interacciones sobre productos i0-i5, más un usuario y un producto
    con pocas interacciones que el k-core debe eliminar."""
    rng = np.random.default_rng(0)
    rows = [
        (f"u{u}", f"i{i}", float(rng.integers(1, 6)), 1_000 * (u * 10 + i))
        for u in range(6)
        for i in range(6)
    ]
    rows += [("u_inactive", "i0", 5.0, 1), ("u0", "i_rare", 4.0, 2)]
    return pd.DataFrame(rows, columns=[USER_ID, ITEM_ID, RATING, TIMESTAMP])


@pytest.fixture
def train_data() -> InteractionData:
    frame = pd.DataFrame(
        {
            USER_IDX: [0, 0, 1, 1, 2],
            ITEM_IDX: [0, 1, 0, 2, 0],
            RATING: [5.0, 4.0, 3.0, 5.0, 4.0],
            TIMESTAMP: [1, 2, 3, 4, 5],
        }
    )
    return InteractionData(frame, n_users=3, n_items=4)
