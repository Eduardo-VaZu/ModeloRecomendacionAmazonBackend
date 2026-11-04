"""Caso de uso: resultados de la evaluación (O1 vs. O2)."""

from __future__ import annotations

from ..shared.base_data_transfer import NoRequest
from ..shared.base_handler import BaseHandler
from .experiment_responses import ExperimentResultResponse, ExperimentResultsResponse


class GetExperimentResultsHandler(BaseHandler[NoRequest, ExperimentResultsResponse]):
    """Devuelve todas las métricas guardadas por el pipeline."""

    async def execute(self, request: NoRequest) -> ExperimentResultsResponse:
        results = await self._unit_of_work.experiment_results.get_all()
        return ExperimentResultsResponse(
            items=[ExperimentResultResponse.model_validate(result) for result in results]
        )
