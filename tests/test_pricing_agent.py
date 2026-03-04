"""Integration tests for the Pricing Strategy Agent.

Requires services to be running with seed data.
"""
import pytest
import httpx

PROPERTY_URL = "http://localhost:8000"
PRICING_URL = "http://localhost:8010"
GATEWAY_URL = "http://localhost:8090"


@pytest.fixture
async def client():
    async with httpx.AsyncClient(timeout=120.0) as c:
        yield c


@pytest.mark.asyncio
async def test_pricing_agent_health(client):
    resp = await client.get(f"{PRICING_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_pricing_analysis(client):
    """Test the full pricing analysis flow.

    1. Get an existing listing
    2. Send it to the pricing agent
    3. Verify the response structure
    """
    # Get a listing to analyze
    resp = await client.get(f"{PROPERTY_URL}/api/v1/listings", params={"limit": 1})
    assert resp.status_code == 200
    listings = resp.json()

    if listings["total"] == 0:
        pytest.skip("No listings in database. Run `make seed` first.")

    listing_id = listings["items"][0]["id"]

    # Analyze via pricing agent
    resp = await client.post(
        f"{PRICING_URL}/api/v1/pricing/analyze",
        json={"property_id": listing_id},
    )
    assert resp.status_code == 200
    result = resp.json()

    # Validate response structure
    assert "recommended_price" in result
    assert "price_range_low" in result
    assert "price_range_high" in result
    assert "confidence" in result
    assert "justification" in result
    assert "comps_used" in result

    assert result["recommended_price"] > 0
    assert result["price_range_low"] <= result["recommended_price"]
    assert result["price_range_high"] >= result["recommended_price"]
    assert result["confidence"] in ("low", "medium", "high")
    assert len(result["justification"]) > 10


@pytest.mark.asyncio
async def test_pricing_via_gateway(client):
    """Test pricing analysis through the API gateway."""
    resp = await client.get(f"{PROPERTY_URL}/api/v1/listings", params={"limit": 1})
    if resp.json()["total"] == 0:
        pytest.skip("No listings. Run `make seed` first.")

    listing_id = resp.json()["items"][0]["id"]

    resp = await client.post(
        f"{GATEWAY_URL}/api/v1/agents/pricing/analyze",
        json={"property_id": listing_id},
    )
    assert resp.status_code == 200
    assert "recommended_price" in resp.json()
