"""Contraste de hipótesis sobre métricas por usuario (3.4.1 de la tesis).

Para cada indicador calculado por usuario (I7, I8, I9, I10, I12) se forman pares (O1, O2) sobre
los mismos usuarios y se prueba la normalidad de las diferencias d = O2 − O1 con Shapiro-Wilk:

- d normal (p >= α) → t-Student para muestras relacionadas.
- d no normal (p < α) → Wilcoxon de rangos con signo.

La meta de cada indicador exige además una mejora relativa >= `min_relative_improvement`
respecto al modelo de referencia. La cobertura (I11) produce un solo valor por modelo y se
reporta de forma descriptiva, fuera de esta prueba.

Con miles de usuarios casi cualquier diferencia es significativa, así que cada prueba reporta
también el tamaño del efecto:

- Wilcoxon: r = Z / √N, con Z de la aproximación normal y N = pares con diferencia distinta de 0.
  Umbrales de Cohen (1988): |r| < 0.1 despreciable, < 0.3 pequeño, < 0.5 mediano, >= 0.5 grande.
- t pareada: d_z = media(d) / DE(d). Umbrales: < 0.2 despreciable, < 0.5 pequeño, < 0.8 mediano.

El signo del efecto sigue al de O2 − O1: negativo significa que el híbrido empeora.
"""

from __future__ import annotations

import warnings
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy import stats

from recsys.config import StatisticsConfig

# Hipótesis específicas → indicadores contrastados (Matriz de Consistencia)
HYPOTHESES = {
    "HE1": ("precision", "recall"),  # exactitud predictiva: I7, I8
    "HE2": ("ndcg", "mrr"),  # calidad del ranking: I9, I10
    "HE3": ("ild",),  # diversificación: I12 (I11 es descriptivo)
}
INDICATORS = {"precision": "I7", "recall": "I8", "ndcg": "I9", "mrr": "I10", "ild": "I12"}


_R_THRESHOLDS = ((0.1, "despreciable"), (0.3, "pequeño"), (0.5, "mediano"))
_D_THRESHOLDS = ((0.2, "despreciable"), (0.5, "pequeño"), (0.8, "mediano"))


def _magnitude(value: float, thresholds: tuple[tuple[float, str], ...]) -> str:
    if not np.isfinite(value):
        return "—"
    return next((label for limit, label in thresholds if abs(value) < limit), "grande")


@dataclass(frozen=True)
class PairedTestResult:
    metric: str
    n_pairs: int
    mean_o1: float
    mean_o2: float
    sd_o1: float
    sd_o2: float
    median_o1: float
    median_o2: float
    relative_improvement: float
    n_improved: int  # usuarios con O2 > O1
    n_tied: int  # usuarios con O2 = O1 (Wilcoxon los descarta)
    n_worse: int  # usuarios con O2 < O1
    shapiro_p: float
    normal: bool
    test: str
    statistic: float
    p_value: float
    effect_size: float
    effect_size_name: str
    effect_magnitude: str
    significant: bool
    meets_goal: bool


def paired_test(
    o1: np.ndarray, o2: np.ndarray, config: StatisticsConfig, metric: str = ""
) -> PairedTestResult:
    """Shapiro-Wilk sobre d = O2 − O1 y, según el resultado, t pareada o Wilcoxon."""
    o1, o2 = np.asarray(o1, dtype=float), np.asarray(o2, dtype=float)
    if o1.shape != o2.shape:
        raise ValueError("O1 y O2 deben tener los mismos usuarios")
    differences = o2 - o1
    mean_o1, mean_o2 = float(o1.mean()), float(o2.mean())
    relative = (mean_o2 - mean_o1) / mean_o1 if mean_o1 else np.inf if mean_o2 > 0 else 0.0

    effect, effect_name, magnitude = np.nan, "—", "—"
    if len(differences) < 3 or np.allclose(differences, differences[0]):
        # Sin variación no hay prueba posible: no se rechaza H0.
        shapiro_p, normal, test, statistic, p_value = np.nan, False, "sin variación", np.nan, 1.0
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # scipy avisa que p es aproximado con n > 5000
            shapiro_p = float(stats.shapiro(differences).pvalue)
        normal = shapiro_p >= config.alpha
        if normal:
            test = "t-Student muestras relacionadas"
            result = stats.ttest_rel(o2, o1, alternative=config.alternative)
            effect, effect_name = float(differences.mean() / differences.std(ddof=1)), "d_z"
            magnitude = _magnitude(effect, _D_THRESHOLDS)
        else:
            test = "Wilcoxon rangos con signo"
            result = stats.wilcoxon(o2, o1, alternative=config.alternative, zero_method="wilcox")
            n_nonzero = int(np.count_nonzero(differences))
            z = stats.wilcoxon(
                o2, o1, alternative=config.alternative, zero_method="wilcox", method="approx"
            ).zstatistic
            effect, effect_name = float(z / np.sqrt(n_nonzero)), "r"
            magnitude = _magnitude(effect, _R_THRESHOLDS)
        statistic, p_value = float(result.statistic), float(result.pvalue)

    significant = p_value < config.alpha
    return PairedTestResult(
        metric=metric,
        n_pairs=len(differences),
        mean_o1=mean_o1,
        mean_o2=mean_o2,
        sd_o1=float(o1.std(ddof=1)) if len(o1) > 1 else np.nan,
        sd_o2=float(o2.std(ddof=1)) if len(o2) > 1 else np.nan,
        median_o1=float(np.median(o1)),
        median_o2=float(np.median(o2)),
        relative_improvement=float(relative),
        n_improved=int((differences > 0).sum()),
        n_tied=int((differences == 0).sum()),
        n_worse=int((differences < 0).sum()),
        shapiro_p=shapiro_p,
        normal=normal,
        test=test,
        statistic=statistic,
        p_value=p_value,
        effect_size=effect,
        effect_size_name=effect_name,
        effect_magnitude=magnitude,
        significant=significant,
        meets_goal=significant and relative >= config.min_relative_improvement,
    )


def hypothesis_table(
    pre: pd.DataFrame, post: pd.DataFrame, config: StatisticsConfig, user_col: str
) -> pd.DataFrame:
    """Una fila por indicador y K, agrupada por hipótesis específica.

    `pre` y `post` son las tablas por usuario de O1 y O2 (columnas `metric@k`).
    """
    paired = pre.merge(post, on=user_col, suffixes=("_o1", "_o2"), validate="one_to_one")
    if len(paired) != len(pre) or len(paired) != len(post):
        raise ValueError("O1 y O2 deben evaluarse sobre exactamente los mismos usuarios")

    rows = []
    for hypothesis, metrics in HYPOTHESES.items():
        for column in pre.columns:
            metric, _, k = column.partition("@")
            if metric not in metrics or column not in post:
                continue
            result = paired_test(paired[f"{column}_o1"], paired[f"{column}_o2"], config, column)
            rows.append(
                {"hypothesis": hypothesis, "indicator": INDICATORS[metric], "k": int(k)}
                | asdict(result)
            )
    return pd.DataFrame(rows)


def descriptive_table(per_user: dict[str, pd.DataFrame], user_col: str) -> pd.DataFrame:
    """Estadística descriptiva por modelo e indicador (ficha de registro de métricas).

    Una fila por (modelo, métrica, K): n, media, DE, mínimo, Q1, mediana, Q3, máximo y la
    proporción de usuarios con valor 0 (la que hace que los datos no sean normales).
    """
    rows = []
    for model, frame in per_user.items():
        for column in frame.columns:
            if column == user_col:
                continue
            metric, _, k = column.partition("@")
            values = frame[column].to_numpy(dtype=float)
            q1, median, q3 = np.percentile(values, [25, 50, 75])
            rows.append(
                {
                    "model": model,
                    "indicator": INDICATORS.get(metric, ""),
                    "metric": metric,
                    "k": int(k),
                    "n": len(values),
                    "mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)) if len(values) > 1 else np.nan,
                    "min": float(values.min()),
                    "q1": float(q1),
                    "median": float(median),
                    "q3": float(q3),
                    "max": float(values.max()),
                    "pct_zero": float((values == 0).mean()),
                }
            )
    return pd.DataFrame(rows)
