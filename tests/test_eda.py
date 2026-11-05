"""Análisis exploratorio (Fase 02): embudo, calificaciones, meses y cola larga."""

import pandas as pd
import pytest

from recsys.data.eda import funnel_table, long_tail_stats, monthly_counts, rating_distribution
from recsys.schema import ITEM_ID, RATING, TIMESTAMP, USER_ID


@pytest.fixture
def interactions() -> pd.DataFrame:
    # u0 ve 4 ítems, u1 ve 2; el ítem a concentra 2 de las 6 interacciones.
    return pd.DataFrame(
        {
            USER_ID: ["u0", "u0", "u0", "u0", "u1", "u1"],
            ITEM_ID: ["a", "b", "c", "d", "a", "e"],
            RATING: [5.0, 4.0, 3.0, 1.0, 5.0, 5.0],
            TIMESTAMP: [
                int(pd.Timestamp(day, tz="UTC").timestamp() * 1000)
                for day in ("2022-01-05", "2022-01-20", "2022-02-01", "2022-02-02",
                            "2022-02-28", "2022-03-01")
            ],
        }
    )


def test_funnel_counts_each_stage_and_share_of_previous(interactions):
    only_u0 = interactions[interactions[USER_ID] == "u0"]
    table = funnel_table([("todo", interactions), ("u0", only_u0)])

    assert table["reviews"].tolist() == [6, 4]
    assert table["users"].tolist() == [2, 1]
    assert table["items"].tolist() == [5, 4]
    assert pd.isna(table.loc[0, "pct_of_previous"])
    assert table.loc[1, "pct_of_previous"] == pytest.approx(4 / 6 * 100)


def test_rating_distribution_marks_relevant_ratings(interactions):
    table = rating_distribution(interactions, threshold=4.0).set_index("rating")

    assert table.loc[5.0, "n"] == 3
    assert table["pct"].sum() == pytest.approx(100)
    assert table.loc[table["relevant"], "pct"].sum() == pytest.approx(4 / 6 * 100)


def test_monthly_counts_group_by_utc_month(interactions):
    table = monthly_counts(interactions)

    assert table["month"].tolist() == ["2022-01", "2022-02", "2022-03"]
    assert table["n"].tolist() == [2, 3, 1]


def test_long_tail_stats(interactions):
    stats = long_tail_stats(interactions)

    assert stats["user_interactions_min"] == 2
    assert stats["user_interactions_max"] == 4
    assert stats["pct_items_single_interaction"] == pytest.approx(80)  # 4 de 5 ítems
    assert stats["pct_interactions_top_1pct_items"] == pytest.approx(2 / 6 * 100)  # el ítem a
