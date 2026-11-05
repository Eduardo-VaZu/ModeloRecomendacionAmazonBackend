.PHONY: up down logs psql add-migration install-python integration-test demo-synthetic \
	demo-export seed download preprocess tune train evaluate figures eda pipeline test lint

# Python del entorno del pipeline (Windows: .venv/Scripts/python; Linux/macOS: make PY=.venv/bin/python)
PY ?= .venv/Scripts/python

up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f

psql:
	docker compose exec db psql -U postgres -d recommender

add-migration:
	docker compose exec backend bash -c "uv run alembic revision --autogenerate -m '$(name)'"

install-python:
	docker compose exec backend uv add $(name)
	docker compose cp backend:/code/pyproject.toml ./backend/pyproject.toml
	docker compose cp backend:/code/uv.lock ./backend/uv.lock

integration-test:
	docker compose exec backend uv run pytest src/test -v

# Paquete de datos del prototipo
demo-synthetic:
	$(PY) scripts/dev_synthetic_demo.py

demo-export:
	$(PY) scripts/06_export_demo.py

seed:
	docker compose exec backend uv run python -m src.seed

# Pipeline de ML (CRISP-DM). Tras `tune`, copiar best_params.json a configs/config.yaml.
download:
	$(PY) scripts/01_download.py

preprocess:
	$(PY) scripts/02_preprocess.py

tune:
	$(PY) scripts/04_tune.py

train:
	$(PY) scripts/03_train.py

evaluate:
	$(PY) scripts/05_evaluate.py

figures:
	$(PY) scripts/07_figures.py

eda:
	$(PY) scripts/08_eda.py

# Con los hiperparámetros ya fijados en config.yaml: muestra → modelos → resultados → figuras.
pipeline: preprocess train evaluate figures eda

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src scripts tests
