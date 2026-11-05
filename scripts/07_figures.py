"""Paso 7: figuras del Capítulo IV a partir de las tablas de `reports/tables/`.

No entrena ni evalúa nada: solo lee los CSV que dejan 04_tune y 05_evaluate y escribe PNG
(300 ppp) en `reports/figures/`.

- `fig1_o1_vs_o2.png`: O1 (popularidad) vs. O2 (híbrido) en I7-I12 con K = 10.
- `fig2_pares_por_usuario.png`: por indicador, % de usuarios que mejoran, empatan o empeoran.
- `fig3_cobertura_vs_ild.png`: diversidad del catálogo (I11) vs. diversidad intra-lista (I12).
- `fig4_ajuste_hibrido.png`: NDCG@10 en validación según candidatos (Etapa 1) y peso I5.

Cada modelo tiene siempre el mismo color en todas las figuras.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from recsys.config import load_config  # noqa: E402
from recsys.utils.logging import get_logger  # noqa: E402

logger = get_logger("07_figures")

K = 10
PRE, POST = "popularity", "hybrid"

# Paleta categórica de referencia (orden fijo, validado para daltonismo) y tinta del gráfico.
MODEL_COLORS = {
    "hybrid": "#2a78d6",
    "popularity": "#eb6834",
    "als": "#1baf7a",
    "content_based": "#eda100",
    "item_mean": "#e87ba4",
}
MODEL_LABELS = {
    "hybrid": "O2: híbrido",
    "popularity": "O1: popularidad",
    "als": "Etapa 2: ALS",
    "content_based": "Etapa 1: contenido",
    "item_mean": "Media por producto",
}
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
IMPROVE, TIE, WORSE = "#2a78d6", "#d6d5cf", "#e34948"  # divergente azul-gris-rojo
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

INDICATORS = [  # (indicador, métrica, nombre, es porcentaje)
    ("I7", "precision", "Precision@10", False),
    ("I8", "recall", "Recall@10", False),
    ("I9", "ndcg", "NDCG@10", False),
    ("I10", "mrr", "MRR@10", False),
    ("I11", "coverage", "Cobertura@10 (%)", True),
    ("I12", "ild", "ILD@10", False),
]

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "text.color": INK,
        "axes.edgecolor": BASELINE,
        "axes.labelcolor": INK_2,
        "axes.titlesize": 10,
        "axes.titlecolor": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "legend.frameon": False,
    }
)


def _fmt(value: float, percent: bool) -> str:
    return f"{value:.2f} %" if percent else (f"{value:.4f}" if value < 0.1 else f"{value:.3f}")


def fig1_o1_vs_o2(results: pd.DataFrame, tests: pd.DataFrame) -> plt.Figure:
    """Una pequeña gráfica por indicador (cada una con su escala): O1 vs. O2 con K = 10."""
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.6))
    tests = tests[tests["k"] == K].set_index("metric")
    for ax, (code, metric, name, percent) in zip(axes.ravel(), INDICATORS, strict=True):
        scale = 100 if percent else 1
        values = [results.loc[model, f"{metric}@{K}"] * scale for model in (PRE, POST)]
        bars = ax.bar(
            [0, 1], values, width=0.6, color=[MODEL_COLORS[PRE], MODEL_COLORS[POST]],
            edgecolor=SURFACE, linewidth=2,
        )
        for bar, value in zip(bars, values, strict=True):
            ax.annotate(_fmt(value, percent), (bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                        fontsize=8, color=INK)
        ax.set_xticks([0, 1], ["O1", "O2"])
        ax.set_ylim(0, max(values) * 1.25)
        ax.yaxis.grid(True, color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", labelsize=7)

        ratio = values[1] / values[0] if values[0] else np.inf
        detail = f"×{ratio:.0f}" if ratio >= 10 else f"{ratio - 1:+.0%}"
        if f"{metric}@{K}" in tests.index:
            row = tests.loc[f"{metric}@{K}"]
            detail += f" · {row['effect_size_name']} = {row['effect_size']:.2f}"
            detail += " · p < 0.001" if row["p_value"] < 0.001 else f" · p = {row['p_value']:.3f}"
        else:
            detail += " · descriptivo"
        ax.set_title(f"{code} {name}\n", loc="left", fontsize=9, fontweight="bold")
        ax.text(0, 1.02, detail, transform=ax.transAxes, fontsize=7.5, color=INK_2)

    handles = [plt.Rectangle((0, 0), 1, 1, color=MODEL_COLORS[m]) for m in (PRE, POST)]
    fig.legend(handles, [MODEL_LABELS[PRE], MODEL_LABELS[POST]], loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return fig


def fig2_pairs(tests: pd.DataFrame) -> plt.Figure:
    """% de usuarios en que O2 mejora, empata o empeora frente a O1 (K = 10)."""
    rows = tests[tests["k"] == K].copy()
    order = ["I7", "I8", "I9", "I10", "I12"]
    rows = rows.set_index("indicator").loc[order[::-1]]
    shares = rows[["n_improved", "n_tied", "n_worse"]].div(rows["n_pairs"], axis=0) * 100
    names = {code: name for code, _, name, _ in INDICATORS}
    labels = [f"{code} {names[code]}" for code in rows.index]
    segments = (
        ("n_improved", IMPROVE, "O2 mejora"),
        ("n_tied", TIE, "Empate (Wilcoxon lo descarta)"),
        ("n_worse", WORSE, "O2 empeora"),
    )

    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    left = np.zeros(len(rows))
    for column, color, name in segments:
        values = shares[column].to_numpy()
        ax.barh(labels, values, left=left, color=color, edgecolor=SURFACE, linewidth=2,
                height=0.62, label=name)
        for y, (start, width) in enumerate(zip(left, values, strict=True)):
            if width >= 6:
                ink = "#ffffff" if color != TIE else INK
                ax.text(start + width / 2, y, f"{width:.0f} %", ha="center", va="center",
                        fontsize=7.5, color=ink)
            elif width > 0 and column == "n_worse":
                ax.text(101, y, f"{width:.1f} %", ha="left", va="center", fontsize=7.5,
                        color=INK_2, clip_on=False)
        left += values
    ax.set_xlim(0, 100)
    ax.set_xlabel(f"% de los {int(rows['n_pairs'].iloc[0])} usuarios evaluados")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=3, fontsize=8)
    fig.tight_layout()
    return fig


def fig3_coverage_vs_ild(results: pd.DataFrame) -> plt.Figure:
    """Cada modelo como punto: cobertura del catálogo (eje x, log) vs. ILD (eje y)."""
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    offsets = {"hybrid": (8, -12), "popularity": (8, 4), "als": (8, 4),
               "content_based": (-8, 6), "item_mean": (8, -12)}
    for model in MODEL_COLORS:
        x = results.loc[model, f"coverage@{K}"] * 100
        y = results.loc[model, f"ild@{K}"]
        ax.scatter(x, y, s=70, color=MODEL_COLORS[model], edgecolor=SURFACE, linewidth=2, zorder=3)
        dx, dy = offsets[model]
        ax.annotate(f"{MODEL_LABELS[model]}\n{x:.2f} % · ILD {y:.3f}", (x, y), xytext=(dx, dy),
                    textcoords="offset points", fontsize=7.5, color=INK,
                    ha="right" if dx < 0 else "left", va="center")
    ax.set_xscale("log")
    ax.set_xlim(0.03, 300)
    ax.set_ylim(0.65, 1.0)
    ax.set_xlabel("I11 Cobertura del catálogo @10 (% de ítems, escala log)")
    ax.set_ylabel("I12 ILD@10 (diversidad intra-lista)")
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xticks([0.1, 1, 10, 100], ["0.1 %", "1 %", "10 %", "100 %"])
    fig.tight_layout()
    return fig


def fig4_tuning(tuning: pd.DataFrame, metric: str) -> plt.Figure:
    """Mapa de calor de NDCG@10 en validación: candidatos × peso de combinación (I5)."""
    grid = tuning.pivot(index="n_candidates", columns="blend_weight", values=metric).sort_index()
    cmap = LinearSegmentedColormap.from_list("azul", BLUES)
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    image = ax.imshow(grid.to_numpy(), cmap=cmap, aspect="auto")
    best = np.unravel_index(np.nanargmax(grid.to_numpy()), grid.shape)
    middle = np.nanmean(grid.to_numpy())
    for (i, j), value in np.ndenumerate(grid.to_numpy()):
        ink = "#ffffff" if value > middle else INK
        weight = "bold" if (i, j) == best else "normal"
        ax.text(j, i, f"{value:.4f}", ha="center", va="center", fontsize=7.5, color=ink,
                fontweight=weight)
    ax.add_patch(plt.Rectangle((best[1] - 0.5, best[0] - 0.5), 1, 1, fill=False,
                               edgecolor=INK, linewidth=1.5))
    ax.set_xticks(range(grid.shape[1]), [f"{w:g}" for w in grid.columns])
    ax.set_yticks(range(grid.shape[0]), [str(n) for n in grid.index])
    ax.set_xlabel("I5 Peso de combinación (peso de ALS)")
    ax.set_ylabel("Candidatos de la Etapa 1")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    bar = fig.colorbar(image, ax=ax, fraction=0.04, pad=0.02)
    bar.set_label(f"{metric.upper()} en validación", color=INK_2)
    bar.outline.set_visible(False)
    fig.tight_layout()
    return fig


def main() -> None:
    config = load_config()
    tables, output = config.paths.tables, config.paths.reports / "figures"
    output.mkdir(parents=True, exist_ok=True)

    results = pd.read_csv(tables / "results.csv").set_index("model")
    tests = pd.read_csv(tables / "hypothesis_tests.csv")
    tuning = pd.read_csv(tables / "tuning_hybrid.csv")

    figures = {
        "fig1_o1_vs_o2.png": fig1_o1_vs_o2(results, tests),
        "fig2_pares_por_usuario.png": fig2_pairs(tests),
        "fig3_cobertura_vs_ild.png": fig3_coverage_vs_ild(results),
        "fig4_ajuste_hibrido.png": fig4_tuning(tuning, config.tuning.metric),
    }
    for name, figure in figures.items():
        figure.savefig(output / name, dpi=300, bbox_inches="tight")
        plt.close(figure)
        logger.info("Figura: %s", output / name)


if __name__ == "__main__":
    main()
