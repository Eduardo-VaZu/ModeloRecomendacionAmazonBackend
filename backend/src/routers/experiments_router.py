"""Endpoints de resultados experimentales y resumen del dataset."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ..use_cases.experiments import (
    DatasetSummaryResponse,
    ExperimentResultsResponse,
    GetDatasetSummaryHandler,
    GetExperimentResultsHandler,
    GetHypothesisTestsHandler,
    GetViIndicatorsHandler,
    HypothesisTestsResponse,
    ViIndicatorsResponse,
)
from ..use_cases.shared.base_data_transfer import NoRequest

experiments_router = APIRouter(prefix="/experiments", tags=["experiments"])


@experiments_router.get("/results", response_model=ExperimentResultsResponse)
async def get_results(
    handler: Annotated[GetExperimentResultsHandler, Depends()],
) -> ExperimentResultsResponse:
    """Métricas de todos los modelos (tabla O1 vs. O2)."""
    return await handler.execute(NoRequest())


@experiments_router.get("/hypothesis-tests", response_model=HypothesisTestsResponse)
async def get_hypothesis_tests(
    handler: Annotated[GetHypothesisTestsHandler, Depends()],
) -> HypothesisTestsResponse:
    """Contraste de HE1-HE3: Shapiro-Wilk, Wilcoxon o t pareada, p, tamaño del efecto y meta."""
    return await handler.execute(NoRequest())


@experiments_router.get("/vi-indicators", response_model=ViIndicatorsResponse)
async def get_vi_indicators(
    handler: Annotated[GetViIndicatorsHandler, Depends()],
) -> ViIndicatorsResponse:
    """Indicadores de la variable independiente (I1-I6)."""
    return await handler.execute(NoRequest())


@experiments_router.get("/summary", response_model=DatasetSummaryResponse)
async def get_summary(
    handler: Annotated[GetDatasetSummaryHandler, Depends()],
) -> DatasetSummaryResponse:
    """Origen y tamaño del dataset del prototipo."""
    return await handler.execute(NoRequest())
