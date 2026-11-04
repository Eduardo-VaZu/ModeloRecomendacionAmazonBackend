"""R7: traduce puntajes de preferencia a ratings 1-5 para medir RMSE y MAE (Fase 4).

`implicit` no predice ratings: optimiza preferencias ponderadas por confianza. Esta capa ajusta
una regresión de scikit-learn (puntaje ALS, puntaje de contenido, sesgos) → rating usando solo
datos de entrenamiento, y recorta la salida al rango [1, 5].
"""

from __future__ import annotations

import numpy as np

RATING_MIN, RATING_MAX = 1.0, 5.0


class RatingCalibrator:
    def fit(self, features: np.ndarray, ratings: np.ndarray) -> RatingCalibrator:
        raise NotImplementedError("Fase 4: calibración de puntajes")

    def predict(self, features: np.ndarray) -> np.ndarray:
        raise NotImplementedError("Fase 4: calibración de puntajes")
