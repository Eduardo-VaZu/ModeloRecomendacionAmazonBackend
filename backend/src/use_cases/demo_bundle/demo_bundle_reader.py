"""Lectura y validación de los archivos del paquete demo."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ...persistency.database.models import (
    DatasetSummary,
    DemoUser,
    ExperimentResult,
    Interaction,
    Product,
    Recommendation,
)


class DemoBundleReader:
    """Convierte cada archivo del paquete en entidades validadas."""

    def __init__(self, directory: Path) -> None:
        if not (directory / "summary.json").exists():
            raise FileNotFoundError(f"No hay un paquete demo en {directory}")
        self._directory = directory

    def summary(self) -> DatasetSummary:
        """Resumen del dataset (`summary.json`)."""
        data = json.loads((self._directory / "summary.json").read_text(encoding="utf-8"))
        return DatasetSummary.model_validate(data)

    def products(self) -> list[Product]:
        """Productos referenciados por el historial y las recomendaciones."""
        return [Product.model_validate(row) for row in self._rows("products")]

    def users(self) -> list[DemoUser]:
        """Usuarios de la muestra."""
        return [DemoUser.model_validate(row) for row in self._rows("users")]

    def interactions(self) -> list[Interaction]:
        """Historial; `timestamp` viene en milisegundos desde 1970 (UTC)."""
        return [
            Interaction.model_validate(
                {**row, "reviewed_at": datetime.fromtimestamp(row["timestamp"] / 1000, tz=UTC)}
            )
            for row in self._rows("interactions")
        ]

    def recommendations(self) -> list[Recommendation]:
        """Top-K precalculado por usuario y modelo."""
        return [Recommendation.model_validate(row) for row in self._rows("recommendations")]

    def experiment_results(self) -> list[ExperimentResult]:
        """Métricas de evaluación por modelo."""
        return [ExperimentResult.model_validate(row) for row in self._rows("experiment_results")]

    def _rows(self, table: str) -> Iterator[dict[str, Any]]:
        with (self._directory / f"{table}.jsonl").open(encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    yield json.loads(line)
