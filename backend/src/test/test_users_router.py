"""Integración de `/users` contra Postgres real."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_supports_search(http_client: AsyncClient, demo_data: None) -> None:
    response = await http_client.get("/users", params={"search": "u1"})

    assert response.status_code == 200
    assert response.json() == {"items": [{"userId": "U1", "nInteractions": 5}], "total": 1}


@pytest.mark.asyncio
async def test_history_includes_product_and_split(
    http_client: AsyncClient, demo_data: None
) -> None:
    body = (await http_client.get("/users/U1/history")).json()

    assert body["interactions"][0]["product"]["title"] == "Producto 0"
    assert body["interactions"][0]["split"] == "train"


@pytest.mark.asyncio
async def test_recommendations_by_model(http_client: AsyncClient, demo_data: None) -> None:
    body = (await http_client.get("/users/U1/recommendations", params={"model": "hybrid"})).json()

    item = body["items"][0]
    assert body["model"] == "hybrid"
    assert item["product"]["productId"] == "P2"
    assert item["alsScore"] == pytest.approx(0.95)
    assert item["reasonProduct"]["title"] == "Producto 0"


@pytest.mark.asyncio
async def test_pipeline_reports_candidate_rank(http_client: AsyncClient, demo_data: None) -> None:
    body = (await http_client.get("/users/U1/pipeline")).json()

    assert body["nCandidates"] == 300
    assert [c["product"]["productId"] for c in body["candidates"]] == ["P1", "P2"]
    assert body["final"][0]["candidateRank"] == 2


@pytest.mark.asyncio
async def test_unknown_user_returns_404(http_client: AsyncClient, demo_data: None) -> None:
    response = await http_client.get("/users/COLD_START/recommendations")

    assert response.status_code == 404
