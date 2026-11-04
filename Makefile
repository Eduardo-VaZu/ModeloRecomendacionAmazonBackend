.PHONY: up down logs psql add-migration install-python integration-test demo-synthetic demo-export seed

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
	.venv/Scripts/python scripts/dev_synthetic_demo.py

demo-export:
	.venv/Scripts/python scripts/06_export_demo.py

seed:
	docker compose exec backend uv run python -m src.seed
