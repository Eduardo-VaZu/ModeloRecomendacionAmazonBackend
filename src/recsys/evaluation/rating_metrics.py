"""R7: error de reconstrucción del rating."""

import numpy as np


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    errors = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean(errors**2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    errors = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(errors)))
