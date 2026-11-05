"""Contraste de una hipótesis específica para un indicador y un corte K."""

from __future__ import annotations

from sqlmodel import Field

from .base import BaseUUIDModel


class HypothesisTest(BaseUUIDModel, table=True):
    """Resultado de `hypothesis_tests.csv`: O1 (popularidad) vs. O2 (híbrido) por usuario."""

    hypothesis: str = Field(max_length=8)
    """Hipótesis específica contrastada (HE1, HE2 o HE3)."""
    indicator: str = Field(max_length=8)
    """Indicador de la matriz (I7, I8, I9, I10 o I12)."""
    metric: str = Field(max_length=32)
    """Métrica con su corte, p. ej. `ndcg@10`."""
    k: int = Field(ge=1)
    n_pairs: int = Field(ge=0)
    """Usuarios evaluados (pares O1-O2)."""
    mean_o1: float
    mean_o2: float
    relative_improvement: float
    """(O2 − O1) / O1; la meta exige >= 0.10."""
    n_improved: int = Field(ge=0)
    n_tied: int = Field(ge=0)
    n_worse: int = Field(ge=0)
    shapiro_p: float | None = None
    """Valor p de Shapiro-Wilk sobre las diferencias pareadas."""
    test: str = Field(max_length=64)
    """Prueba aplicada (Wilcoxon o t-Student para muestras relacionadas)."""
    statistic: float | None = None
    p_value: float
    effect_size: float | None = None
    effect_size_name: str = Field(default="", max_length=8)
    """`r` (Wilcoxon) o `d_z` (t pareada)."""
    effect_magnitude: str = Field(default="", max_length=16)
    """Magnitud según Cohen: despreciable, pequeño, mediano o grande."""
    significant: bool
    meets_goal: bool
    """p < α y mejora relativa >= 10 %."""
