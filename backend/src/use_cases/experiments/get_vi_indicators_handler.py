"""Caso de uso: indicadores de la variable independiente (I1-I6)."""

from __future__ import annotations

from ..shared.base_data_transfer import NoRequest
from ..shared.base_handler import BaseHandler
from .experiment_responses import ViIndicatorResponse, ViIndicatorsResponse


class GetViIndicatorsHandler(BaseHandler[NoRequest, ViIndicatorsResponse]):
    """Devuelve los parámetros del híbrido (I1-I5) y su tasa de hibridación (I6)."""

    async def execute(self, request: NoRequest) -> ViIndicatorsResponse:
        indicators = await self._unit_of_work.vi_indicators.get_all()
        ordered = sorted(indicators, key=lambda i: (int(i.indicator.removeprefix("I")), i.k or 0))
        return ViIndicatorsResponse(
            items=[ViIndicatorResponse.model_validate(indicator) for indicator in ordered]
        )
