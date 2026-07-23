"""Read-only integration tests against the real (already-scraped) dev DB.

No writes here on purpose -- these run against the same Postgres instance
used for local dev/demo, so they only exercise GET endpoints and assert on
shape/invariants that hold regardless of exactly which reviews are present.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_properties_returns_four(client):
    response = await client.get("/api/properties")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 4
    for prop in body:
        assert prop["id"]
        assert prop["slug"]
        assert prop["name"]


@pytest.mark.asyncio
async def test_property_summary_unknown_id_404s(client):
    response = await client.get("/api/properties/999999/summary")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_property_summary_known_property_shape(client):
    properties = (await client.get("/api/properties")).json()
    prop_id = properties[0]["id"]
    response = await client.get(f"/api/properties/{prop_id}/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["property"]["id"] == prop_id
    assert body["review_count"] >= 0


@pytest.mark.asyncio
async def test_reviews_list_default_pagination(client):
    response = await client.get("/api/reviews")
    assert response.status_code == 200
    body = response.json()
    assert "total" in body
    assert "items" in body
    assert len(body["items"]) <= 50


@pytest.mark.asyncio
async def test_reviews_filtered_by_property(client):
    properties = (await client.get("/api/properties")).json()
    prop_id = properties[0]["id"]
    response = await client.get(f"/api/reviews?property_id={prop_id}")
    assert response.status_code == 200
    body = response.json()
    assert all(item["property_id"] == prop_id for item in body["items"])


@pytest.mark.asyncio
async def test_reviews_limit_is_capped_at_200(client):
    response = await client.get("/api/reviews?limit=9999")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reviews_pagination_offset_moves_window(client):
    page1 = (await client.get("/api/reviews?limit=2&offset=0")).json()
    page2 = (await client.get("/api/reviews?limit=2&offset=2")).json()
    ids1 = {item["id"] for item in page1["items"]}
    ids2 = {item["id"] for item in page2["items"]}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_weekly_summary_shape(client):
    response = await client.get("/api/insights/weekly-summary")
    assert response.status_code == 200
    body = response.json()
    assert "current_week_avg_rating" in body
    assert "previous_week_avg_rating" in body
    assert "delta" in body


@pytest.mark.asyncio
async def test_topic_insights_shape(client):
    response = await client.get("/api/insights/topics")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    for item in body["items"]:
        assert "topic" in item
        assert "negative_count" in item
        assert "positive_count" in item


@pytest.mark.asyncio
async def test_health_reports_all_flags(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) >= {
        "status",
        "database",
        "llm_classification_enabled",
        "apify_fallback_configured",
        "scrape_endpoint_enabled",
    }


@pytest.mark.asyncio
async def test_scrape_status_unknown_property_404s(client):
    response = await client.get("/api/properties/999999/scrape-status")
    assert response.status_code == 404
