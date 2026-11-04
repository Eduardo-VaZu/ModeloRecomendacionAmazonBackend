"""R9: cobertura del catálogo."""

import numpy as np


def catalog_coverage(recommended: np.ndarray, n_items: int) -> float:
    """Proporción de productos del catálogo que aparece en al menos una recomendación."""
    return len(np.unique(recommended)) / n_items
