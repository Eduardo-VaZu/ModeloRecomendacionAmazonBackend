"""Caso de uso: contraste de las hipótesis específicas (HE1-HE3)."""

from __future__ import annotations

from ..shared.base_data_transfer import NoRequest
from ..shared.base_handler import BaseHandler
from .experiment_responses import HypothesisTestResponse, HypothesisTestsResponse


def _indicator_number(code: str) -> int:
    """`I10` → 10, para ordenar I7 < I8 < ... < I12."""
    return int(code.removeprefix("I") or 0)


class GetHypothesisTestsHandler(BaseHandler[NoRequest, HypothesisTestsResponse]):
    """Devuelve las pruebas de hipótesis calculadas por el pipeline (05_evaluate)."""

    async def execute(self, request: NoRequest) -> HypothesisTestsResponse:
        tests = await self._unit_of_work.hypothesis_tests.get_all()
        ordered = sorted(tests, key=lambda t: (t.hypothesis, _indicator_number(t.indicator), t.k))
        return HypothesisTestsResponse(
            items=[HypothesisTestResponse.model_validate(test) for test in ordered]
        )
