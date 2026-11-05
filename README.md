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
| 3. Entrenamiento | `python scripts/03_train.py` | Pendiente (05_evaluate ya entrena cada modelo) |
| 4. Hiperparámetros (validación) | `python scripts/04_tune.py` | Listo |
| 5. Evaluación (test) | `python scripts/05_evaluate.py` | O1, contenido, ALS e híbrido (O2) listos; tabla pre/post en la Fase 6 |
| 6. Paquete del prototipo | `python scripts/06_export_demo.py` | O1 listo; contenido, ALS e híbrido pendientes |

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
| R3 | Etapa 1: contenido | `models/content_based.py`, `features/text_features.py` | `tests/test_content_based.py` |
| R4 | Etapa 2: ALS (implícito + explícito) | `models/als.py` | `tests/test_als.py` |
| R5 | Híbrido en dos etapas | `models/hybrid.py` | `tests/test_hybrid.py` |
| R6 | Python + scikit-learn + Implicit | `requirements.txt` | `tests/test_scope.py` |
| R7 | RMSE y MAE vs. no personalizados | `evaluation/rating_metrics.py`, `models/calibration.py` | `tests/test_metrics.py`, `tests/test_als.py` |
| R8 | Precision@K, Recall@K, F1@K | `evaluation/ranking_metrics.py` | `tests/test_metrics.py` |
| R9 | Cobertura del catálogo | `evaluation/coverage.py` | `tests/test_metrics.py` |
| R10 | Tiempo de entrenamiento (s) | `Recommender.fit` + `utils/timing.py` | `tests/test_baselines.py` |
| R11 | Sin deep learning ni LLM | Alcance | `tests/test_scope.py` |
| R12 | Diseño O1 × X × O2 | `experiments/pre_post.py` | `tests/test_metrics.py` |
| R13 | Duplicados y completitud ≥ 90 % | `data/quality.py` | `tests/test_quality.py` |
| R14 | Costo computacional de ALS | Columna `train_time_s` | Tabla de resultados |

## Decisiones metodológicas

- **Partición temporal por usuario:** las interacciones más recientes de cada usuario van a test y las anteriores a validación. Nunca se usa información del futuro.
- **Reentrenamiento para test:** los hiperparámetros se eligen en validación; para la evaluación final, cada modelo (O1 y O2) se reentrena con train + validación y se mide en test. En Video_Games, entrenar solo con train dejaba al modelo de contenido con R@10 = 0,0171 en test, frente a 0,0235 con train + validación; la popularidad casi no cambiaba (0,0276 frente a 0,0281). La diferencia se debe a la distancia temporal entre el historial y las compras de test.
- **Relevancia:** un producto de test cuenta como relevante si su rating es mayor o igual a `relevance_threshold` (4 por defecto).
- **F1@K:** es la media armónica de Precision@K y Recall@K, ambas promediadas entre usuarios.
- **RMSE y MAE con ALS:** `implicit` no predice ratings, así que una regresión lineal de scikit-learn (puntaje ALS, media del usuario, media del producto) calibra los puntajes a la escala de 1 a 5. Para no sesgarla, se aparta la última interacción de cada usuario dentro de train, se entrena un ALS auxiliar con el resto y la regresión se ajusta sobre esas interacciones apartadas.
- **Confianza de ALS (R4):** preferencia 1 si la interacción existe (señal implícita) y confianza c = 1 + α · rating / 5 (señal explícita).
- **Híbrido (R5):** el contenido elige `n_candidates` productos no vistos y el puntaje final es `blend_weight · ALS + (1 − blend_weight) · contenido`, ambos llevados a [0, 1] entre los candidatos. El rating estimado mezcla los de cada etapa con el mismo peso.
- **Ajuste de hiperparámetros:** `04_tune.py` recorre en validación las grillas de `config.yaml → tuning` y elige por F1@10. Los valores elegidos (ALS con 128 factores y α = 40; 3.000 candidatos; peso 0,85) quedaron en el borde de la grilla, así que ampliarla podría mejorarlos un poco.
- **Completitud (R13):** se mide por campo de metadatos (I1 = valores no nulos / valores esperados), no por producto. Los campos que no llegan al 90 % (en Video_Games, `features` y `description`) se conservan, y sus valores faltantes se imputan con texto vacío al construir el texto de la Etapa 1. Ningún producto se elimina por completitud. Los porcentajes quedan en `quality_report.json`.
- **Estado de conversión (exclusión B2B):** no aplica, porque Amazon Reviews 2023 no tiene ese campo.

## Limitaciones

- **Cold start:** está excluido por el filtro de mínimo 5 interacciones.
- **Sin deep learning ni agentes LLM:** es una decisión de alcance.
- **Diseño pre-experimental sin grupo de control:** factores externos como la estacionalidad no están controlados.
- **Costo computacional:** ALS requiere más tiempo de cómputo que los modelos no personalizados.
- **Techo de la Etapa 1:** ALS solo reordena los candidatos que elige el contenido. Con 3.000 candidatos, el híbrido queda un 3,6 % por debajo de ALS solo en F1@10 (0,0186 frente a 0,0193 en test), pero cubre un 44 % más del catálogo (21,9 % frente a 15,2 % en cobertura@10).

## Resultados en test (Video_Games)

Cada modelo se entrena con train + validación. La tabla completa, con K = 5, 10 y 20, está en `reports/tables/results.csv`.

| Modelo | RMSE | MAE | F1@10 | Cobertura@10 | Entrenamiento |
|---|---:|---:|---:|---:|---:|
| O1: popularidad | 1,263 | 0,982 | 0,0066 | 0,07 % | 0,007 s |
| O1: media por producto | 1,216 | 0,913 | 0,0002 | 0,05 % | 0,009 s |
| Etapa 1: contenido | 1,176 | 0,779 | 0,0053 | 81,9 % | 24,5 s |
| Etapa 2: ALS | 1,112 | 0,792 | 0,0193 | 15,2 % | 21,3 s |
| O2: híbrido | 1,112 | 0,787 | 0,0186 | 21,9 % | 46,5 s |

## Pendientes

1. **Tabla pre/post (R12, Fase 6):** armar la comparación O1 frente a O2 con la diferencia de cada indicador, a partir de `results.csv`, en `experiments/pre_post.py` y `05_evaluate.py`.
2. **Prototipo con datos reales:** agregar contenido, ALS e híbrido a `06_export_demo.py`, con el puntaje de cada etapa (`content_score`, `als_score`) y el producto del historial que explica cada recomendación (`reason_product_id`). Después, volver a correr `make seed` para reemplazar los datos sintéticos.
3. **Notebook de exploración (EDA, Fase 1):** distribución de ratings, interacciones por usuario y por producto (cola larga), evolución en el tiempo, largo de los textos y conteos de cada paso del preprocesamiento.
4. **`03_train.py`:** sigue sin implementar. Solo hace falta para guardar los modelos entrenados en disco; hoy `05_evaluate.py` entrena cada modelo antes de medirlo.
5. **Rutas de datos:** `config.yaml` apunta a `D:/TESIS-data`, que solo existe en esta máquina. Para reproducir en otra, hay que cambiar las rutas o crear esa carpeta.
6. **Opcional, ampliar la grilla de ajuste:** 128 factores y 3.000 candidatos quedaron en el borde de la grilla. Más candidatos acercan el híbrido a ALS solo y le quitan peso al filtro de contenido.

## Tests

```bash
pytest
```
