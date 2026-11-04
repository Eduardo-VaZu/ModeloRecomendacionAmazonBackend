# Recomendador híbrido para Amazon (contenido + ALS)

Modelo de recomendación en dos etapas sobre **Amazon Reviews 2023**:

1. **Etapa 1, filtrado basado en contenido:** TF-IDF de los textos de cada producto (scikit-learn) para generar candidatos.
2. **Etapa 2, factorización de matrices con ALS:** la librería `implicit` reordena los candidatos combinando interacciones implícitas y explícitas.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
```

## Pipeline

| Paso | Script | Estado |
|---|---|---|
| 1. Descarga | `python scripts/01_download.py` | Listo |
| 2. Calidad → k-core → split | `python scripts/02_preprocess.py` | Listo |
| 3. Entrenamiento | `python scripts/03_train.py` | Fases 3-5 |
| 4. Hiperparámetros (validación) | `python scripts/04_tune.py` | Fase 5 |
| 5. Evaluación (test) | `python scripts/05_evaluate.py` | O1 listo; O2 en la Fase 6 |

Todos los parámetros están en [`configs/config.yaml`](configs/config.yaml).

## Trazabilidad de requisitos

| # | Requisito | Implementación | Verificación |
|---|---|---|---|
| R1 | Amazon Reviews 2023 | `data/loader.py` | `config.yaml → dataset` |
| R2 | Mínimo 5 interacciones | `data/preprocessing.py` (k-core iterativo) | `tests/test_kcore.py`; `config.py` rechaza k < 5 |
| R3 | Etapa 1: contenido | `models/content_based.py`, `features/text_features.py` | Fase 3 |
| R4 | Etapa 2: ALS (implícito + explícito) | `models/als.py` | Fase 4 |
| R5 | Híbrido en dos etapas | `models/hybrid.py` | Fase 5 |
| R6 | Python + scikit-learn + Implicit | `requirements.txt` | `tests/test_scope.py` |
| R7 | RMSE y MAE vs. no personalizados | `evaluation/rating_metrics.py`, `models/calibration.py` | `tests/test_metrics.py` |
| R8 | Precision@K, Recall@K, F1@K | `evaluation/ranking_metrics.py` | `tests/test_metrics.py` |
| R9 | Cobertura del catálogo | `evaluation/coverage.py` | `tests/test_metrics.py` |
| R10 | Tiempo de entrenamiento (s) | `Recommender.fit` + `utils/timing.py` | `tests/test_baselines.py` |
| R11 | Sin deep learning ni LLM | Alcance | `tests/test_scope.py` |
| R12 | Diseño O1 × X × O2 | `experiments/pre_post.py` | `tests/test_metrics.py` |
| R13 | Duplicados y completitud ≥ 90 % | `data/quality.py` | `tests/test_quality.py` |
| R14 | Costo computacional de ALS | Columna `train_time_s` | Tabla de resultados |

## Decisiones metodológicas

- **Partición temporal por usuario:** las interacciones más recientes de cada usuario van a test y las anteriores a validación. Nunca se usa información del futuro.
- **Relevancia:** un producto de test cuenta como relevante si su rating es mayor o igual a `relevance_threshold` (4 por defecto).
- **F1@K:** es la media armónica de Precision@K y Recall@K, ambas promediadas entre usuarios.
- **RMSE y MAE con ALS:** `implicit` no predice ratings, así que una regresión de scikit-learn calibra los puntajes a la escala de 1 a 5, usando solo datos de entrenamiento.
- **Estado de conversión (exclusión B2B):** no aplica, porque Amazon Reviews 2023 no tiene ese campo.

## Limitaciones

- **Cold start:** está excluido por el filtro de mínimo 5 interacciones.
- **Sin deep learning ni agentes LLM:** es una decisión de alcance.
- **Diseño pre-experimental sin grupo de control:** factores externos como la estacionalidad no están controlados.
- **Costo computacional:** ALS requiere más tiempo de cómputo que los modelos no personalizados.

## Tests

```bash
pytest
```
