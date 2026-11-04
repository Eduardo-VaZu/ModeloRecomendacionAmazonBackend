"""Integración de `/experiments` contra Postgres real."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_results(http_client: AsyncClient, demo_data: None) -> None:
    body = (await http_client.get("/experiments/results")).json()

    assert body["items"] == [{"model": "hybrid", "metric": "rmse", "k": None, "value": 0.95}]


@pytest.mark.asyncio
async def test_summary_flags_synthetic_data(http_client: AsyncClient, demo_data: None) -> None:
    body = (await http_client.get("/experiments/summary")).json()

    assert body["isSynthetic"] is True
    assert body["nCandidates"] == 300


@pytest.mark.asyncio
async def test_summary_without_bundle_returns_404(http_client: AsyncClient) -> None:
    response = await http_client.get("/experiments/summary")

    assert response.status_code == 404
