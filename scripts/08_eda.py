"""Paso 8 (CRISP-DM, Fase 02): análisis exploratorio del dataset para la tesis.

Repite los filtros de 02_preprocess sobre los datos crudos para contar cuánto queda en cada paso,
y describe la muestra final. Necesita `raw/` (01_download) y `processed/` (02_preprocess).

Tablas en `reports/tables/`:
- `eda_funnel.csv`: reseñas, usuarios e ítems después de cada paso de la preparación.
- `eda_ratings.csv`: distribución de las calificaciones de la muestra.
- `eda_monthly.csv`: interacciones de la muestra por mes.
- `eda_summary.json`: resumen (calificaciones, cola larga, densidad, particiones, metadatos).

Figuras en `reports/figures/`:
- `fig5_embudo_muestra.png`, `fig6_calificaciones.png`, `fig7_cola_larga.png`,
  `fig8_interacciones_mes.png`.
"""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from recsys.config import load_config
from recsys.data.eda import funnel_table, long_tail_stats, monthly_counts, rating_distribution
from recsys.data.loader import raw_paths, read_jsonl
from recsys.data.preprocessing import filter_active_users, filter_period, sample_report
from recsys.data.quality import apply_quality_rules
from recsys.data.storage import load_splits
from recsys.plots import DPI, INK, INK_2, MUTED, PRIMARY, SURFACE, apply_style, value_grid
from recsys.schema import ITEM_ID, META_COLUMNS, RATING, REVIEW_COLUMNS, USER_ID
from recsys.utils.logging import get_logger

logger = get_logger("08_eda")

STAGE_LABELS = (
    "Reseñas de Video_Games\n(Amazon Reviews 2023)",
    "Periodo ene-2022 a sep-2023",
    "Calidad: una por par usuario-ítem,\ncon metadatos",
    "Usuarios con ≥ 5 interacciones\n(muestra)",
)


def _thousands(value: float) -> str:
    return f"{value:,.0f}"


def fig_funnel(funnel: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    y = np.arange(len(funnel))[::-1]
    ax.barh(y, funnel["reviews"], color=PRIMARY, height=0.6, edgecolor=SURFACE, linewidth=2)
    top = funnel["reviews"].max()
    for yi, row in zip(y, funnel.itertuples(), strict=True):
        previous = row.pct_of_previous
        share = "" if np.isnan(previous) else f"  ({previous:.1f} % del paso anterior)"
        ax.text(row.reviews + top * 0.01, yi,
                f"{_thousands(row.reviews)} reseñas{share}\n"
                f"{_thousands(row.users)} usuarios · {_thousands(row.items)} ítems",
                va="center", fontsize=7.5, color=INK)
    ax.set_yticks(y, STAGE_LABELS[: len(funnel)])
    ax.set_xlim(0, top * 1.75)
    ax.set_xticks([])
    ax.spines[["left", "bottom"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    return fig


def fig_ratings(ratings: pd.DataFrame, threshold: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    colors = [PRIMARY if relevant else MUTED for relevant in ratings["relevant"]]
    stars = ratings["rating"].astype(int).to_numpy()
    bars = ax.bar(stars, ratings["pct"], color=colors, width=0.62, edgecolor=SURFACE, linewidth=2)
    ax.set_xticks(stars)
    for bar, row in zip(bars, ratings.itertuples(), strict=True):
        ax.annotate(f"{row.pct:.1f} %\n({_thousands(row.n)})",
                    (bar.get_x() + bar.get_width() / 2, row.pct), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=7.5, color=INK)
    relevant = ratings.loc[ratings["relevant"], "pct"].sum()
    ax.set_title(f"Relevantes (calificación ≥ {threshold:g}): {relevant:.1f} %", loc="left",
                 fontsize=9, color=INK_2)
    ax.set_xlabel("Calificación (estrellas)")
    ax.set_ylabel("% de interacciones")
    ax.set_ylim(0, ratings["pct"].max() * 1.3)
    value_grid(ax)
    fig.tight_layout()
    return fig


def fig_long_tail(sample: pd.DataFrame) -> plt.Figure:
    per_user = sample[USER_ID].value_counts()
    per_item = sample[ITEM_ID].value_counts().to_numpy()
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.2, 2.9))

    bins = np.arange(per_user.min(), min(per_user.max(), 60) + 2) - 0.5
    left.hist(per_user.clip(upper=60), bins=bins, color=PRIMARY, edgecolor=SURFACE, linewidth=0.8)
    left.set_yscale("log")
    left.set_xlabel("Interacciones por usuario (≥ 60 agrupado)")
    left.set_ylabel("Usuarios (escala log)")
    left.set_title(f"Mediana: {np.median(per_user):g} por usuario", loc="left", fontsize=9,
                   color=INK_2)
    value_grid(left)

    rank = np.arange(1, len(per_item) + 1)
    right.plot(rank, per_item, color=PRIMARY, linewidth=2)
    right.set_xscale("log")
    right.set_yscale("log")
    right.set_xlabel("Ítems ordenados por popularidad (escala log)")
    right.set_ylabel("Interacciones (escala log)")
    single = (per_item == 1).mean() * 100
    right.set_title(f"{single:.0f} % de los ítems tiene 1 sola interacción", loc="left",
                    fontsize=9, color=INK_2)
    value_grid(right, "both")
    fig.tight_layout()
    return fig


def fig_monthly(monthly: pd.DataFrame) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    x = np.arange(len(monthly))
    ax.plot(x, monthly["n"], color=PRIMARY, linewidth=2, marker="o", markersize=4,
            markeredgecolor=SURFACE, markeredgewidth=1)
    quarters = ("-01", "-04", "-07", "-10")
    ticks = [i for i, month in enumerate(monthly["month"]) if month.endswith(quarters)]
    ax.set_xticks(ticks, [monthly["month"].iloc[i] for i in ticks])
    ax.set_ylabel("Interacciones de la muestra")
    ax.set_ylim(0, monthly["n"].max() * 1.15)
    value_grid(ax)
    fig.tight_layout()
    return fig


def main() -> None:
    apply_style()
    config = load_config()
    reviews_path, meta_path = raw_paths(config.dataset, config.paths.raw)
    reviews = read_jsonl(reviews_path, REVIEW_COLUMNS)
    meta = read_jsonl(meta_path, META_COLUMNS)
    logger.info("Leídos: %d reseñas, %d productos", len(reviews), len(meta))

    in_period = filter_period(reviews, config.period.start, config.period.end)
    clean, _, quality = apply_quality_rules(
        in_period, meta, config.quality.meta_completeness_fields, config.quality.min_completeness
    )
    sample = filter_active_users(clean, config.filtering.min_user_interactions)
    funnel = funnel_table(
        list(zip(STAGE_LABELS, (reviews, in_period, clean, sample), strict=True))
    )
    funnel["stage"] = funnel["stage"].str.replace("\n", " ")
    ratings = rating_distribution(sample, config.evaluation.relevance_threshold)
    monthly = monthly_counts(sample)

    splits = load_splits(config.paths.processed)
    split_sizes = {name: len(data.frame) for name, data in splits.items()}
    summary = {
        "sample": sample_report(sample, len(in_period)),
        "rating_mean": float(sample[RATING].mean()),
        "rating_sd": float(sample[RATING].std()),
        "pct_relevant": float(ratings.loc[ratings["relevant"], "pct"].sum()),
        "long_tail": long_tail_stats(sample),
        "splits": split_sizes | {"train_plus_val": split_sizes["train"] + split_sizes["val"]},
        "meta_field_completeness": quality["meta_field_completeness"],
        "reviews_duplicated": quality["reviews_duplicated"],
    }

    tables, figures = config.paths.tables, config.paths.reports / "figures"
    for directory in (tables, figures):
        directory.mkdir(parents=True, exist_ok=True)
    funnel.to_csv(tables / "eda_funnel.csv", index=False)
    ratings.to_csv(tables / "eda_ratings.csv", index=False)
    monthly.to_csv(tables / "eda_monthly.csv", index=False)
    (tables / "eda_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Embudo:\n%s", funnel.to_string(index=False))
    logger.info("Resumen: %s", json.dumps(summary, ensure_ascii=False))

    for name, figure in {
        "fig5_embudo_muestra.png": fig_funnel(funnel),
        "fig6_calificaciones.png": fig_ratings(ratings, config.evaluation.relevance_threshold),
        "fig7_cola_larga.png": fig_long_tail(sample),
        "fig8_interacciones_mes.png": fig_monthly(monthly),
    }.items():
        figure.savefig(figures / name, dpi=DPI, bbox_inches="tight")
        plt.close(figure)
        logger.info("Figura: %s", figures / name)


if __name__ == "__main__":
    main()
