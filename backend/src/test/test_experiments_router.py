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


@pytest.mark.asyncio
async def test_hypothesis_tests_are_ordered_by_hypothesis_indicator_and_k(
    http_client: AsyncClient, demo_data: None
) -> None:
    body = (await http_client.get("/experiments/hypothesis-tests")).json()

    order = [(t["hypothesis"], t["k"]) for t in body["items"]]
    assert order == [("HE1", 5), ("HE1", 10), ("HE3", 10)]
    he3 = body["items"][-1]
    assert he3["metric"] == "ild@10"
    assert he3["meetsGoal"] is False
    assert he3["effectSizeName"] == "r"
    assert he3["nTied"] == 85


@pytest.mark.asyncio
async def test_vi_indicators_are_ordered(http_client: AsyncClient, demo_data: None) -> None:
    body = (await http_client.get("/experiments/vi-indicators")).json()

    assert [i["indicator"] for i in body["items"]] == ["I1", "I6"]
    assert body["items"][0]["k"] is None
    assert body["items"][1]["value"] == 0.46


@pytest.mark.asyncio
async def test_new_tables_are_empty_without_bundle(http_client: AsyncClient) -> None:
    tests = (await http_client.get("/experiments/hypothesis-tests")).json()
    indicators = (await http_client.get("/experiments/vi-indicators")).json()

    assert tests["items"] == []
    assert indicators["items"] == []
