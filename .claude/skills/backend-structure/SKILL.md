---
name: backend-structure
description: Reference for the Python FastAPI backend layout in `backend/`. Use whenever adding/modifying endpoints, use cases, repositories, database models, Alembic migrations, or integration tests — covers the layered architecture (routers → handlers → unit-of-work → repositories → models), base classes, naming conventions, package exports, config wiring, the docker-compose stack, and Make targets.
---
# Backend Structure

The backend lives in backend/ and follows a layered, handler-per-use-case architecture on top of FastAPI + SQLModel + async SQLAlchemy. Alembic handles migrations. Configuration comes from environment variables via `pydantic-settings`. The whole stack (Postgres + pgAdmin + migrations + backend) is orchestrated by `docker-compose.yml` at the repo root.

## Tech stack

- **Runtime**: Python `>=3.14`, `uv` for dependency/lock management (`uv.lock`, `pyproject.toml`)
- **Web**: `fastapi`, served by `uvicorn`
- **ORM**: `sqlmodel` (SQLModel = SQLAlchemy + Pydantic) over async SQLAlchemy with `psycopg` (v3) async driver
- **Migrations**: `alembic`
- **Settings**: `pydantic-settings`
- **Tests**: `pytest` + `pytest-asyncio` + `httpx.AsyncClient` (ASGITransport)

## Directory layout

```
backend/
├── Dockerfile                # multi-stage: `dev` (uvicorn reload) + `migration` (alembic upgrade head)
├── alembic.ini               # Alembic config (script_location → src/alembic)
├── pyproject.toml            # project + deps (managed by uv)
├── uv.lock
└── src/
    ├── main.py               # ASGI entrypoint — imports `app` from bootstrap and registers feature routers
    ├── bootstrap.py          # FastAPI() instance, CORS middleware, `/healthcheck` endpoint
    ├── config.py             # `ConfigurationVariables` pydantic-settings (POSTGRES_URL, LOG_SQL_QUERIES)
    ├── database.py           # async engine, sessionmaker, `AsyncSQLSession` FastAPI dependency
    ├── alembic/              # migrations
    │   ├── env.py            # imports `src.persistency.database.models` + uses SQLModel.metadata
    │   ├── script.py.mako
    │   └── versions/
    ├── routers/              # FastAPI APIRouter modules — thin HTTP layer
    │   ├── __init__.py
    │   └── vehicle_telemetry_router.py
    ├── use_cases/            # one handler per use case (business logic)
    │   ├── shared/
    │   │   ├── base_handler.py        # `BaseHandler[TRequest, TResponse]` with UoW
    │   │   └── base_data_transfer.py  # pydantic base w/ camelCase aliases
    │   └── vehicle_telemetry/         # one package per feature
    │       ├── __init__.py            # re-exports handler + DTOs
    │       ├── create_vehicle_telemetry_handler.py
    │       ├── vehicle_telemetry_request.py
    │       └── vehicle_telemetry_response.py
    ├── persistency/
    │   ├── unit_of_work.py            # aggregates repositories on a single AsyncSession
    │   ├── repositories/
    │   │   ├── base_repository.py     # generic CRUD: get_all/get_by_id/create/update/delete/bulk_create
    │   │   └── vehicle_telemetry_repository.py
    │   └── database/
    │       └── models/
    │           ├── __init__.py        # MUST re-export every model so Alembic autogenerate sees them
    │           ├── vehicle_telemetry.py
    │           └── base/
    │               ├── base_model.py       # `__tablename__` = snake_case(class name)
    │               ├── base_uuid_model.py  # UUID PK with `default_factory=uuid4`
    │               └── snake_case.py
    └── test/                  # integration tests (hit the real DB through the ASGI app)
        ├── __init__.py
        ├── conftest.py        # `http_client` fixture + autouse table cleanup
        └── test_vehicle_telemetry_router.py
```

## Architectural layers (request flow)

```
HTTP request
  → routers/*.py                            (FastAPI APIRouter — validates request, picks handler)
  → use_cases/<feature>/<verb>_handler.py   (extends BaseHandler, orchestrates logic)
  → persistency/unit_of_work.py             (UnitOfWork wraps one AsyncSession, exposes repos)
  → persistency/repositories/*              (extend BaseRepository[Entity])
  → persistency/database/models/            (SQLModel entities, mapped to tables)
  → PostgreSQL (async via psycopg)
```

Keep routers thin — translate HTTP ↔ DTO and delegate to a handler. Keep handlers framework-agnostic — they receive an `AsyncSQLSession` and operate via `self._unit_of_work`.

## Core conventions

### DTOs — `BaseDataTransfer`
- All request/response models extend `use_cases.shared.base_data_transfer.BaseDataTransfer`
- Configured with `alias_generator=to_camel`, `populate_by_name=True`, `from_attributes=True`
  → Python uses `snake_case`, JSON uses `camelCase`, models can be built directly from ORM entities via `model_validate`.

### Handlers — `BaseHandler[TRequest, TResponse]`
- Generic over a `TRequest`/`TResponse` pair (both `BaseDataTransfer`)
- Constructed with FastAPI's `AsyncSQLSession`, builds a `UnitOfWork` internally
- Implements `async def execute(self, request: TRequest) -> TResponse`
- Pattern inside `execute`: build ORM entity from `request.model_dump()`, call a repo on `self._unit_of_work`, return `Response.model_validate(entity)`.

### Repositories — `BaseRepository[TEntity]`
- Set `_entity_class` on the subclass (one-liner is fine)
- Provides `get_all`, `get_by_id`, `create`, `update`, `delete`, `bulk_create`
- Each repository takes the active `AsyncSession`; do NOT open new sessions inside.

### Unit of Work
- `UnitOfWork(session)` instantiates every repository against the same session.
- Add new repos by adding a typed attribute + an assignment in `__init__`.

### Models — `BaseModel` / `BaseUUIDModel`
- Inherit from `BaseUUIDModel` for entities with a UUID primary key (`id`, indexed, `default_factory=uuid4`).
- Table names are derived automatically from the class name via `snake_case(cls.__name__)` — do NOT set `__tablename__` manually.
- Every new model MUST be imported in `src/persistency/database/models/__init__.py` so `alembic/env.py`'s `from ... import *` picks it up for autogenerate.
- Use `sa_column=Column(JSONB, ...)` for list/dict fields, `Field(ge=..., le=...)` for numeric constraints, `StrEnum` for closed-set status fields.

### Use case packages
- Each feature lives in `use_cases/<feature>/` with its own `__init__.py` that re-exports the public surface (handler + DTOs).
- Routers then import everything they need in a single `from ..use_cases.<feature> import (...)` statement.

### Routers and app wiring
- Routers go in `src/routers/<feature>_router.py`. Use `APIRouter(prefix="/<feature>", tags=["..."])`.
- Inject the handler via `Depends()` — FastAPI resolves the `AsyncSQLSession → get_session` chain automatically.
- Register routers in **`main.py`** (not `bootstrap.py`) via `app.include_router(...)`. `bootstrap.py` only owns the `FastAPI()` app, CORS, and the `/healthcheck` endpoint.

### Config
- `ConfigurationVariables` reads env vars with explicit aliases:
  - `POSTGRES_URL` → `database_url`
  - `LOG_SQL_QUERIES` → `log_sql_queries` (default `False`)
- `database.py` rewrites `postgresql:` → `postgresql+psycopg:` so SQLAlchemy picks the async driver.

### Tests
- Live in `src/test/` as a package.
- `conftest.py` provides an `http_client` fixture (`httpx.AsyncClient` + `ASGITransport(app=app)` — no real network) and an autouse cleanup fixture that truncates the feature's table after each test.
- Mark async tests with `@pytest.mark.asyncio`.
- Tests hit the **real Postgres** via the same `POSTGRES_URL`, so the stack must be up and migrations applied.

## Adding a new feature — checklist

1. **Model**: create `src/persistency/database/models/<entity>.py` extending `BaseUUIDModel`; re-export it from `models/__init__.py`.
2. **Migration**: `make add-migration name="<msg>"`, review the generated file in `src/alembic/versions/`. The `migrations` compose service applies pending migrations on `make up`.
3. **Repository**: add `src/persistency/repositories/<entity>_repository.py` extending `BaseRepository[<Entity>]` with `_entity_class = <Entity>`. Register it in `UnitOfWork`.
4. **DTOs**: define request/response classes extending `BaseDataTransfer` under `use_cases/<feature>/`.
5. **Handler**: add `<verb>_<entity>_handler.py` extending `BaseHandler[Req, Resp]`, implement `execute`.
6. **Package exports**: in `use_cases/<feature>/__init__.py`, re-export the handler and DTOs.
7. **Router**: in `src/routers/````<feature>_router.py`, expose an endpoint that depends on the handler (FastAPI `Depends`).
8. **Register router**: in `main.py`, `app.include_router(<feature>_router)`.
9. **Test**: add `src/test/test_<feature>_router.py` using the `http_client` fixture; rely on the autouse cleanup or add your own.

## Running and operating the stack

The repo root has a `Makefile` and a `docker-compose.yml`. The compose stack defines four services:

- **`db`** — `postgres:16`, healthcheck via `pg_isready`.
- **`migrations`** — built from `backend/`, `target: migration`, runs `alembic upgrade head` once and exits. `backend` waits on `service_completed_successfully`.
- **`pgadmin`** — `dpage/pgadmin4` at `localhost:8080`, pre-configured with the `Local Postgres` server via `./pgadmin/servers.json` + `./pgadmin/pgpass`.
- **`backend`** — built from `backend/`, `target: dev`, exposed on `localhost:8000`. Mounts `./backend/src` and `./backend/alembic.ini` for hot-reload. Healthchecked via `curl -f http://localhost:8000/healthcheck`.

### `.env` (repo root)
Drives both compose and the app:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`, `POSTGRES_HOST` — DB credentials.
- `POSTGRES_URL` — full connection string (e.g. `postgresql://postgres:postgres@db:5432/mydb`). Consumed by the backend container.
- `DATABASE_URL` — `${VAR}`-interpolated mirror for clients/loaders that support dotenv expansion.
- `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`, `PGADMIN_CONFIG_SERVER_MODE`, `PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED`.

### Make targets
- `make up` — `docker compose up -d` (DB → migrations → backend, pgadmin in parallel).
- `make down` — `docker compose down -v` (drops the volume — DB data is lost).
- `make logs` — tail all service logs.
- `make psql` — open a `psql` shell inside the `postgres` container.
- `make add-migration name="<msg>"` — runs `uv run alembic revision --autogenerate -m '<msg>'` inside the backend container.
- `make install-python name="<pkg>"` — runs `uv add <pkg>` inside the backend container, then `docker compose cp`'s `pyproject.toml` and `uv.lock` from `/code` back to `./backend/` on the host so the lockfile stays in sync.
- `make integration-test` — runs `uv run pytest src/test -v` inside the backend container.

## Common pitfalls

- **Alembic doesn't see a new model** → it isn't re-exported from `models/__init__.py`.
- **`postgresql://`**** URL fails async** → `database.py` already rewrites the scheme; if you bypass it, use `postgresql+psycopg://...` explicitly.
- **`config.py`**** references \****`get_database_url`** in \****`alembic/env.py`***\* — that attribute must exist on \****`ConfigurationVariables`***\*. \****`**If you rename database_url, update both places.`**
- **Don't open ad-hoc sessions** in repositories or handlers — always reuse the session from `AsyncSQLSession` / `UnitOfWork` so a single transaction wraps the request.
- **`make install-python`**** doesn't update the host lockfile** → the container's working directory isn't `/code`. The Makefile assumes `/code`; adjust the `docker compose cp` paths if the Dockerfile changes it.
- **`make integration-test`**** truncates the dev DB** → the autouse cleanup fixture deletes from feature tables after each test. Use a dedicated test DB if you have dev data to preserve.
- **Backend healthcheck fails immediately** → the `curl -f` test assumes `curl` is in the `dev` image. Add it to the Dockerfile or swap for `wget --spider -q ...` if it's missing.

## Code Style
- **Naming**: Descriptive yet concise names for variables, methods, and classes
- **Documentation**: Docstrings for all classes, functions, enums, enum values
- **Type hints**: Use consistently; avoid `Any` unless necessary

## Type Annotations
- Use `dict`, `list` instead of `typing.Dict`, `typing.List`
- Use `str | None` instead of `Optional[str]`
- Include `from __future__ import annotations` at top of files with type hints
- Prefer built-in types over typing module equivalents