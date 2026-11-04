"""Instancia de FastAPI, CORS, manejo de errores y `/healthcheck`."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import configuration
from .use_cases.shared.errors import NotFoundError

app = FastAPI(title="Recomendador híbrido Amazon - Prototipo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=configuration.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
async def handle_not_found(_: Request, error: NotFoundError) -> JSONResponse:
    """Traduce `NotFoundError` de los casos de uso a HTTP 404."""
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    """Indica que la API está viva (usado por docker compose)."""
    return {"status": "ok"}
