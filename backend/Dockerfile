FROM python:3.14-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1
WORKDIR /code
COPY pyproject.toml uv.lock* ./
RUN uv sync
COPY alembic.ini ./
COPY src ./src

FROM base AS dev
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS migration
CMD ["uv", "run", "alembic", "upgrade", "head"]
