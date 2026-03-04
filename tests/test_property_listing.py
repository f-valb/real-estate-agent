"""Integration tests for the Property Listing service."""
import pytest
import httpx

PROPERTY_URL = "http://localhost:8000"


@pytest.fixture
async def client():
    async with httpx.AsyncClient(timeout=30.0) as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get(f"{PROPERTY_URL}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_get_listing(client):
    payload = {
        "property_type": "single_family",
        "address_line1": "123 Test St",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "list_price": "450000",
    }
    resp = await client.post(f"{PROPERTY_URL}/api/v1/listings", json=payload)
    assert resp.status_code == 201
    listing = resp.json()
    assert listing["city"] == "Austin"
    assert listing["status"] == "draft"
    listing_id = listing["id"]

    # Get by ID
    resp = await client.get(f"{PROPERTY_URL}/api/v1/listings/{listing_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == listing_id


@pytest.mark.asyncio
async def test_list_listings_with_filter(client):
    resp = await client.get(f"{PROPERTY_URL}/api/v1/listings", params={"city": "Austin", "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_status_transition(client):
    # Create
    payload = {
        "property_type": "condo",
        "address_line1": "456 Status Test",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201",
        "list_price": "300000",
    }
    resp = await client.post(f"{PROPERTY_URL}/api/v1/listings", json=payload)
    listing_id = resp.json()["id"]

    # draft -> active (valid)
    resp = await client.patch(
        f"{PROPERTY_URL}/api/v1/listings/{listing_id}/status",
        json={"status": "active"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    # active -> sold (invalid, must go through pending)
    resp = await client.patch(
        f"{PROPERTY_URL}/api/v1/listings/{listing_id}/status",
        json={"status": "sold"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_404_for_missing_listing(client):
    resp = await client.get(f"{PROPERTY_URL}/api/v1/listings/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
