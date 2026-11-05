"""Estilo común de las figuras de la tesis (07_figures y 08_eda).

Paleta categórica de referencia en orden fijo (validada para daltonismo): cada modelo conserva su
color en todas las figuras. Requiere matplotlib (dependencia de desarrollo).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

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
PRIMARY = "#2a78d6"  # una sola serie
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DPI = 300


def apply_style() -> None:
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


def value_grid(ax: plt.Axes, axis: str = "y") -> None:
    """Rejilla tenue detrás de las marcas; `axis` es "x", "y" o "both"."""
    ax.grid(True, axis=axis, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
