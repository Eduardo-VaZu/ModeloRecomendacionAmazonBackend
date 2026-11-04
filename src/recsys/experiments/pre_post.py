"""R12: diseño pre-experimental O1 × X × O2.

O1 = modelo no personalizado (pre-test), X = modelo híbrido, O2 = híbrido (post-test), medidos
sobre los mismos usuarios y la misma partición. No hay grupo de control paralelo.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

LOWER_IS_BETTER = ("rmse", "mae", "train_time_s")


def pre_post_table(pre: Mapping[str, float], post: Mapping[str, float]) -> pd.DataFrame:
    """Compara cada métrica numérica común entre O1 y O2 e indica si hubo mejora."""
    rows = []
    for metric, o1 in pre.items():
        o2 = post.get(metric)
        if not isinstance(o1, (int, float)) or not isinstance(o2, (int, float)):
            continue
        delta = o2 - o1
        lower_is_better = metric in LOWER_IS_BETTER
        rows.append(
            {
                "metric": metric,
                "O1": o1,
                "O2": o2,
                "delta": delta,
                "delta_pct": 100 * delta / o1 if o1 else np.nan,
                "improved": delta < 0 if lower_is_better else delta > 0,
            }
        )
    return pd.DataFrame(rows)
