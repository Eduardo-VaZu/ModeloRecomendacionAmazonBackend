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
| 6. Paquete del prototipo | `python scripts/06_export_demo.py` | O1 listo; contenido e híbrido en la Fase 5 |

Todos los parámetros están en [`configs/config.yaml`](configs/config.yaml).

## Backend del prototipo visual

La interfaz del prototipo vive en otro repo, **ModeloRecomendacionAmazonFrontend** (React). Este repo le sirve la API.

```
pipeline ML ──06_export_demo──▶ artifacts/demo/*.jsonl ──make seed──▶ Postgres ◀── FastAPI ◀── frontend (otro repo)
```

- `backend/`: FastAPI + SQLModel + Alembic, con capas routers → handlers → unit of work → repositorios. Solo lee recomendaciones precalculadas; no entrena modelos.
- `docker-compose.yml`: servicios `db`, `migrations`, `pgadmin` y `backend`.
- CORS: por defecto acepta `http://localhost:5173` y `http://localhost:5180`. Otros orígenes se agregan con `CORS_ORIGINS` en `.env`.

### Puesta en marcha

Requiere Docker Desktop.

```bash
cp .env.example .env
docker compose up -d --build
python scripts/dev_synthetic_demo.py      # o 06_export_demo.py con datos reales
docker compose exec backend uv run python -m src.seed
```

| Servicio | URL |
|---|---|
| API (Swagger) | http://localhost:8000/docs |
| pgAdmin | http://localhost:8080 |

`dev_synthetic_demo.py` genera **datos sintéticos** que solo sirven para desarrollar la interfaz. La API los marca con `isSynthetic` y el frontend muestra un aviso. Nunca deben usarse como resultados de la tesis.

### Comandos (`Makefile`)

En Windows sin `make`, usa el comando equivalente de la segunda columna.

| `make` | Equivalente |
|---|---|
| `make up` / `make down` | `docker compose up -d` / `docker compose down -v` |
| `make seed` | `docker compose exec backend uv run python -m src.seed` |
| `make add-migration name="x"` | `docker compose exec backend bash -c "uv run alembic revision --autogenerate -m 'x'"` |
| `make install-python name="pkg"` | `docker compose exec backend uv add pkg` y luego copiar `pyproject.toml` y `uv.lock` con `docker compose cp` |
| `make integration-test` | `docker compose exec backend uv run pytest src/test -v` |

`make integration-test` vacía las tablas del prototipo. Después de correrlo, vuelve a ejecutar `make seed`.

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
- **Completitud (R13):** se mide por campo de metadatos (I1 = valores no nulos / valores esperados), no por producto. Los campos que no llegan al 90 % (en Video_Games, `features` y `description`) se conservan, y sus valores faltantes se imputan con texto vacío al construir el texto de la Etapa 1. Ningún producto se elimina por completitud. Los porcentajes quedan en `quality_report.json`.
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
