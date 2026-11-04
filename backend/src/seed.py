"""Importa el paquete demo a Postgres: `uv run python -m src.seed /demo`."""

from __future__ import annotations

import asyncio
import sys

from .database import session_factory
from .use_cases.demo_bundle import ImportDemoBundleHandler, ImportDemoBundleRequest

DEFAULT_DIRECTORY = "/demo"


async def main(directory: str) -> None:
    """Ejecuta el caso de uso de importación fuera de una petición HTTP."""
    async with session_factory() as session:
        response = await ImportDemoBundleHandler(session).execute(
            ImportDemoBundleRequest(directory=directory)
        )
    kind = "SINTÉTICO" if response.is_synthetic else "real"
    print(f"Paquete {kind} importado: {response.model_dump(exclude={'is_synthetic'})}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIRECTORY))
