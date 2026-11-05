# Sistema de recomendación híbrido para Amazon (contenido + ALS)

Prototipo de la tesis *"Sistema de recomendación híbrido con aprendizaje automático para mejorar la personalización de productos de Amazon, 2022-2023"* (UTP, Ingeniería de Software). Recomienda en dos etapas sobre **Amazon Reviews 2023** (Hou et al., 2024), categoría Video_Games:

1. **Etapa 1, filtrado basado en contenido:** TF-IDF de los atributos de cada producto (scikit-learn) para elegir candidatos.
2. **Etapa 2, factorización de matrices con ALS:** la librería `implicit` puntúa esos candidatos, combinando interacciones implícitas y explícitas, y se mezcla con el puntaje de contenido.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .
```

## Pipeline (CRISP-DM)

| Paso | Script | Fase CRISP-DM | Salida en `reports/tables/` |
|---|---|---|---|
| 1. Descarga | `python scripts/01_download.py` | 02 Comprensión de los datos | — |
| 2. Periodo → calidad → usuarios ≥ 5 → partición | `python scripts/02_preprocess.py` | 03 Preparación | `sample_report.json` |
| (opcional) Análisis exploratorio | `python scripts/08_eda.py` | 02 Comprensión de los datos | `eda_*.csv`, `eda_summary.json`, `fig5`-`fig8` |
| 3. Ajuste en validación (I3, I4, I5) | `python scripts/04_tune.py` | 04 Modelado | `tuning_als.csv`, `tuning_hybrid.csv`, `best_params.json` |
| 4. Entrenamiento con train + validación | `python scripts/03_train.py` | 04 Modelado | `vi_parameters.csv` (+ `artifacts/models/`) |
| 5. Pre-Test vs. Post-Test en test | `python scripts/05_evaluate.py` | 05 Evaluación | `results.csv`, `hypothesis_tests.csv`, `descriptive_stats.csv`, `pre_post.csv`, `hybridization_rate.csv`, `technical_validation.csv`, `per_user_metrics.csv` |
| 6. Figuras del Capítulo IV | `python scripts/07_figures.py` | 05 Evaluación | `reports/figures/*.png` |
| 7. Paquete del prototipo | `python scripts/06_export_demo.py` | 06 Despliegue | `artifacts/demo/` |

Orden: 01 → 02 → 04 → copiar `best_params.json` a `configs/config.yaml` → 03 → 05 → 07 → 06 (08 cuando se quiera, después de 02). Con los hiperparámetros ya fijados, `make pipeline` corre 02 → 03 → 05 → 07 → 08. Todos los parámetros están en [`configs/config.yaml`](configs/config.yaml).

## Trazabilidad con la Matriz de Consistencia

| Elemento de la matriz | Implementación | Salida | Test |
|---|---|---|---|
| Población: Video_Games, ene-2022 a sep-2023 | `data/preprocessing.py::filter_period` | `sample_report.json` | `tests/test_sample.py` |
| Muestra: usuarios con ≥ 5 interacciones, una por par usuario-ítem (los ítems no se filtran) | `filter_active_users`, `quality.py::drop_duplicate_interactions` | `sample_report.json` | `tests/test_sample.py` |
| Partición train-test 80/20 por usuario | `data/splitting.py::temporal_user_split` | `train/val/test.parquet` | `tests/test_splitting.py` |
| Relevante = calificación ≥ 4; solo usuarios con ≥ 1 relevante | `evaluation/evaluator.py` | — | `tests/test_baselines.py` |
| VI-D1 · I1 atributos de ítem, I2 dimensión del vector | `models/content_based.py`, `features/text_features.py` | `vi_parameters.csv` | `tests/test_content_based.py`, `tests/test_matrix_indicators.py` |
| VI-D2 · I3 factores latentes, I4 regularización | `models/als.py` | `vi_parameters.csv` | `tests/test_als.py` |
| VI-D3 · I5 peso de combinación | `models/hybrid.py` | `vi_parameters.csv`, `tuning_hybrid.csv` | `tests/test_hybrid.py` |
| VI-D3 · I6 tasa de hibridación del ranking | `evaluation/hybridization.py` | `hybridization_rate.csv` | `tests/test_metrics.py` |
| VD-D1 · I7 Precision@K, I8 Recall@K | `evaluation/ranking_metrics.py` | `results.csv`, `per_user_metrics.csv` | `tests/test_metrics.py` |
| VD-D2 · I9 NDCG@K, I10 MRR@K | `evaluation/ranking_metrics.py` | `results.csv`, `per_user_metrics.csv` | `tests/test_metrics.py` |
| VD-D3 · I11 Coverage@K (descriptivo) | `evaluation/coverage.py` | `results.csv` | `tests/test_metrics.py` |
| VD-D3 · I12 ILD@K | `evaluation/diversity.py` | `results.csv`, `per_user_metrics.csv` | `tests/test_metrics.py` |
| Pre-Test O1 = popularidad; Post-Test O2 = híbrido | `scripts/05_evaluate.py` | `pre_post.csv` | — |
| Shapiro-Wilk sobre diferencias → t pareada o Wilcoxon, α = 0.05; meta ≥ 10 %; tamaño del efecto | `experiments/hypothesis_tests.py` | `hypothesis_tests.csv` | `tests/test_hypothesis.py` |
| Ficha de registro de métricas (Instrumento 05): descriptivos por usuario | `experiments/hypothesis_tests.py::descriptive_table` | `per_user_metrics.csv`, `descriptive_stats.csv` | `tests/test_hypothesis.py` |
| Validación técnica: RMSE, MAE vs. media del ítem; tiempo de ALS | `models/calibration.py`, `models/als.py` | `technical_validation.csv` | `tests/test_als.py`, `tests/test_matrix_indicators.py` |
| Python + scikit-learn + Implicit; sin deep learning ni LLM | `requirements.txt` | — | `tests/test_scope.py` |

Hipótesis → indicadores contrastados: **HE1** I7, I8 · **HE2** I9, I10 · **HE3** I12 (I11 se reporta de forma descriptiva).

## Decisiones metodológicas

- **Orden de la Fase 03:** periodo → registros incompletos → una interacción por par usuario-ítem (la más reciente) → ítems sin metadatos → usuarios con ≥ 5 interacciones. `sample_report.json` permite compararlo con la tesis (6,869 usuarios, 15,710 ítems, 53,593 interacciones). Verificado con los datos reales: coincide exactamente.
- **Partición temporal por usuario:** test es el 20 % más reciente de cada usuario (mínimo 1, redondeo hacia abajo). La validación del ajuste es el 20 % más reciente del 80 % restante. Así, test es exactamente el 20 % del 80/20 de la tesis, y train + validación es su 80 %.
- **Reentrenamiento para test:** los hiperparámetros se eligen en validación; para la evaluación final, cada modelo (O1 y O2) se reentrena con train + validación y se mide en test. Con la muestra anterior, entrenar solo con train dejaba al modelo de contenido con R@10 = 0,0171 en test, frente a 0,0235 con train + validación; la popularidad casi no cambiaba (0,0276 frente a 0,0281).
- **Confianza de ALS:** preferencia 1 si la interacción existe (señal implícita) y confianza c = 1 + α · rating / 5 (señal explícita).
- **Híbrido:** el contenido elige `n_candidates` productos no vistos y el puntaje final es `blend_weight · ALS + (1 − blend_weight) · contenido`, ambos llevados a [0, 1] entre los candidatos. El rating estimado mezcla los de cada etapa con el mismo peso.
- **I6:** proporción del Top-K del híbrido que no está en el Top-K de su propio módulo ALS.
- **ILD@K:** 1 − coseno entre los vectores TF-IDF de contenido; los mismos vectores para O1 y O2.
- **Prueba estadística:** unilateral (`alternative: greater`), porque las hipótesis afirman una mejora. Wilcoxon descarta los pares con diferencia 0. Con n > 5000, Shapiro-Wilk da un p aproximado.
- **RMSE y MAE con ALS:** `implicit` no predice ratings, así que una regresión lineal (puntaje ALS, media del usuario, media del producto) calibra los puntajes a la escala de 1 a 5. Para no sesgarla, se aparta la última interacción de cada usuario dentro de train, se entrena un ALS auxiliar con el resto y la regresión se ajusta sobre esas interacciones apartadas. El tiempo de entrenamiento que se reporta (`factorization_time_s`) es solo el de la factorización.
- **Ajuste de hiperparámetros:** `04_tune.py` recorre en validación las grillas de `config.yaml → tuning` y elige por NDCG@10 (I9). F1@10 se sigue calculando, pero ya no es un indicador de la matriz.
- **Completitud de metadatos:** se mide por campo. Los campos que no llegan al 90 % (en Video_Games, `features` y `description`) se conservan, y sus valores faltantes se imputan con texto vacío. Ningún producto se elimina por completitud. Los porcentajes quedan en `quality_report.json`.

## Limitaciones

- **Cold start:** fuera del alcance, porque la muestra exige 5 interacciones por usuario. Los ítems con pocas interacciones sí se conservan; el módulo de contenido es el único que puede recomendarlos.
- **Diseño pre-experimental sin grupo de control:** los resultados no se generalizan más allá del dataset y la muestra.
- **Sin deep learning ni agentes LLM:** es una decisión de alcance.
- **Techo de la Etapa 1:** ALS solo reordena los candidatos que elige el contenido. Con la muestra vigente y 3.000 candidatos, el híbrido supera a ALS solo en NDCG@10 (0,0342 frente a 0,0331) y casi triplica su cobertura (32,2 % frente a 11,4 %).

## Análisis exploratorio (Fase 02)

`scripts/08_eda.py` repite los filtros de la preparación sobre los datos crudos y describe la muestra (`eda_summary.json`, figuras 5-8):

| Paso | Reseñas | Usuarios | Ítems |
|---|---:|---:|---:|
| Video_Games completo | 4.624.615 | 2.766.656 | 137.249 |
| Periodo ene-2022 a sep-2023 | 579.662 (12,5 %) | 434.097 | 47.081 |
| Calidad (8.625 duplicados eliminados) | 571.037 (98,5 %) | 434.097 | 47.081 |
| Usuarios con ≥ 5 interacciones (muestra) | 53.593 (9,4 %) | 6.869 | 15.710 |

- **Calificaciones:** media 4,41 (DE 1,07); el 84,9 % son ≥ 4 (relevantes) y el 68,4 % son 5 estrellas.
- **Cola larga:** mediana de 6 interacciones por usuario; el 54 % de los ítems tiene una sola interacción y el 10 % más popular concentra el 47 % de las interacciones.
- **Tiempo:** la actividad de la muestra cae desde abril de 2023 hasta casi cero en septiembre (fin de la recolección del dataset). Como test toma las interacciones más recientes de cada usuario, conviene mencionarlo como limitación.

## Resultados en test (muestra vigente, Video_Games 2022-2023)

Muestra: 579.662 reseñas del periodo → 6.869 usuarios, 15.710 ítems y 53.593 interacciones (densidad 0,0497 %), igual que la tesis. Se evalúan los 5.910 usuarios con al menos un ítem relevante en test. Hiperparámetros elegidos en validación por NDCG@10: 64 factores, regularización 0,1, α = 10, 3.000 candidatos y peso 0,7. Todas las tablas están en `reports/tables/`.

| Modelo | Precision@10 | Recall@10 | NDCG@10 | MRR@10 | ILD@10 | Cobertura@10 | RMSE | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| O1: popularidad | 0,0027 | 0,0241 | 0,0135 | 0,0110 | 0,969 | 0,08 % | 1,075 | 0,815 |
| O1: media por producto | 0,0007 | 0,0060 | 0,0030 | 0,0023 | 0,952 | 0,08 % | 1,064 | 0,783 |
| Etapa 1: contenido | 0,0040 | 0,0309 | 0,0170 | 0,0141 | 0,729 | 65,6 % | 1,013 | 0,639 |
| Etapa 2: ALS | 0,0071 | 0,0577 | 0,0331 | 0,0280 | 0,931 | 11,4 % | 0,965 | 0,663 |
| O2: híbrido | 0,0077 | 0,0624 | 0,0342 | 0,0280 | 0,882 | 32,2 % | 0,965 | 0,652 |

Contraste O1 vs. O2 (`hypothesis_tests.csv`, K = 10; Shapiro-Wilk rechaza la normalidad en todos los casos → Wilcoxon de rangos con signo, unilateral):

| Hipótesis | Indicador | Mejora relativa | p | Tamaño del efecto r | ¿Cumple la meta? |
|---|---|---:|---:|---:|:---:|
| HE1 | I7 Precision@10 | +189 % | 8,6e-37 | 0,57 (grande) | Sí |
| HE1 | I8 Recall@10 | +159 % | 1,8e-27 | 0,48 (mediano) | Sí |
| HE2 | I9 NDCG@10 | +153 % | 6,8e-24 | 0,43 (mediano) | Sí |
| HE2 | I10 MRR@10 | +154 % | 4,2e-24 | 0,44 (mediano) | Sí |
| HE3 | I12 ILD@10 | −9 % | 1,0 | −0,87 (grande, en contra) | **No** |

r = Z/√N de Wilcoxon (N = pares con diferencia ≠ 0; umbrales de Cohen 0,1 / 0,3 / 0,5). En I7-I10, el 91-92 % de los usuarios empata (ningún acierto con ninguno de los dos modelos), el 7 % mejora y el 2 % empeora; en I12 empeora el 100 % (`reports/figures/fig2_pares_por_usuario.png`).

- **HE3:** la lista de popularidad tiene un ILD alto porque sus 10 ítems son muy distintos entre sí, pero es la misma para todos los usuarios (cobertura 0,08 %). El híbrido personaliza: sus listas son más homogéneas por dentro (ILD 0,882), pero cubre 389 veces más catálogo (I11, descriptivo; `fig3_cobertura_vs_ild.png`). Con I12 como indicador de contraste, HE3 no se acepta.
- **VI:** I1 = 5 atributos, I2 = 50.000 (el vocabulario llega al tope de `max_features`), I3 = 64, I4 = 0,1, I5 = 0,7 e **I6 = 0,46** (el 46 % del Top-10 del híbrido no estaría en el Top-10 de ALS solo).
- **Validación técnica:** RMSE 0,965 frente a 1,064 de la media del ítem (−9 %), MAE 0,652 frente a 0,783 (−17 %). La factorización de ALS tarda 1,0 s.

## Pendientes

1. **Rutas de datos:** `config.yaml` apunta a `D:/TESIS-data`. Para reproducir en otra máquina, hay que cambiar las rutas o crear esa carpeta.
2. **Opcional, ampliar la grilla de ajuste:** 3.000 candidatos (el máximo de la grilla) dio el mejor NDCG@10 en validación.
3. **Opcional, trabajo futuro para HE3:** una etapa de re-ranking por diversidad (p. ej., MMR) que suba el ILD sin perder la exactitud de HE1 y HE2.

HE3 se reporta como no aceptada con I12, y la cobertura (I11) se discute como hallazgo descriptivo. El prototipo ya usa datos reales (`artifacts/demo/`, `make seed`).

## Backend del prototipo visual

La interfaz vive en otro repo, **ModeloRecomendacionAmazonFrontend** (React). Este repo le sirve la API.

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
| `make pipeline` | 02 → 03 → 05 → 07 → 08 con `.venv/Scripts/python` (en Linux/macOS: `make pipeline PY=.venv/bin/python`) |
| `make download` / `preprocess` / `tune` / `train` / `evaluate` / `figures` / `eda` | Cada paso del pipeline por separado |
| `make test` / `make lint` | `pytest` / `ruff check src scripts tests` |

`make integration-test` vacía las tablas del prototipo. Después de correrlo, vuelve a ejecutar `make seed`.

## Tests

```bash
pytest
```
