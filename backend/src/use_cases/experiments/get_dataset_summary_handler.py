"""Caso de uso: resumen del dataset importado."""

from __future__ import annotations

from ..shared.base_data_transfer import NoRequest
from ..shared.base_handler import BaseHandler
from ..shared.errors import NotFoundError
from .experiment_responses import DatasetSummaryResponse


class GetDatasetSummaryHandler(BaseHandler[NoRequest, DatasetSummaryResponse]):
    """Devuelve el origen del paquete demo (y si sus datos son sintéticos)."""

    async def execute(self, request: NoRequest) -> DatasetSummaryResponse:
        summary = await self._unit_of_work.dataset_summaries.get_current()
        if summary is None:
            raise NotFoundError("Aún no se importó ningún paquete demo (make seed)")
        return DatasetSummaryResponse.model_validate(summary)
