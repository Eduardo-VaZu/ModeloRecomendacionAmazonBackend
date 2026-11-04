"""Conjuntos cerrados de valores usados por las entidades."""

from __future__ import annotations

from enum import StrEnum


class RecommenderModel(StrEnum):
    """Modelos evaluados en la tesis."""

    POPULARITY = "popularity"
    """O1: recomienda los productos con más interacciones."""
    ITEM_MEAN = "item_mean"
    """O1: recomienda por rating promedio del producto."""
    CONTENT_BASED = "content_based"
    """Etapa 1: candidatos por similitud de contenido."""
    ALS = "als"
    """Etapa 2 aislada: factorización de matrices ALS."""
    HYBRID = "hybrid"
    """O2: contenido + ALS en dos etapas."""


class DataSplit(StrEnum):
    """Partición temporal a la que pertenece una interacción."""

    TRAIN = "train"
    """Interacciones usadas para entrenar."""
    VAL = "val"
    """Interacciones usadas para ajustar hiperparámetros."""
    TEST = "test"
    """Interacciones más recientes, usadas para evaluar."""
