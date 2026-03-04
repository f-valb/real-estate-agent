"""Integration tests for the CRM Contact service."""
import pytest
import httpx

CRM_URL = "http://localhost:8001"


@pytest.fixture
async def client():
    async with httpx.AsyncClient(timeout=30.0) as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get(f"{CRM_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_get_contact(client):
    payload = {
        "contact_type": "buyer",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@test.com",
        "phone": "512-555-0101",
        "preferences": {"min_price": 300000, "max_price": 600000, "bedrooms": 3},
    }
    resp = await client.post(f"{CRM_URL}/api/v1/contacts", json=payload)
    assert resp.status_code == 201
    contact = resp.json()
    assert contact["first_name"] == "Jane"
    assert contact["pipeline_stage"] == "new"
    contact_id = contact["id"]

    resp = await client.get(f"{CRM_URL}/api/v1/contacts/{contact_id}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "jane.doe@test.com"


@pytest.mark.asyncio
async def test_add_interaction(client):
    # Create contact first
    resp = await client.post(
        f"{CRM_URL}/api/v1/contacts",
        json={"contact_type": "lead", "first_name": "Test", "last_name": "Interaction"},
    )
    contact_id = resp.json()["id"]

    # Add interaction
    resp = await client.post(
        f"{CRM_URL}/api/v1/contacts/{contact_id}/interactions",
        json={"type": "call", "direction": "outbound", "subject": "Initial contact"},
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "call"

    # List interactions
    resp = await client.get(f"{CRM_URL}/api/v1/contacts/{contact_id}/interactions")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_tags(client):
    resp = await client.post(
        f"{CRM_URL}/api/v1/contacts",
        json={"contact_type": "buyer", "first_name": "Tag", "last_name": "Test"},
    )
    contact_id = resp.json()["id"]

    resp = await client.post(
        f"{CRM_URL}/api/v1/contacts/{contact_id}/tags",
        json={"tag": "hot_lead"},
    )
    assert resp.status_code == 201
    assert "hot_lead" in resp.json()


@pytest.mark.asyncio
async def test_pipeline_transition(client):
    resp = await client.post(
        f"{CRM_URL}/api/v1/contacts",
        json={"contact_type": "buyer", "first_name": "Pipeline", "last_name": "Test"},
    )
    contact_id = resp.json()["id"]

    # new -> contacted (valid)
    resp = await client.patch(
        f"{CRM_URL}/api/v1/contacts/{contact_id}/pipeline",
        json={"stage": "contacted"},
    )
    assert resp.status_code == 200
    assert resp.json()["pipeline_stage"] == "contacted"

    # contacted -> proposal (invalid, must go through qualified)
    resp = await client.patch(
        f"{CRM_URL}/api/v1/contacts/{contact_id}/pipeline",
        json={"stage": "proposal"},
    )
    assert resp.status_code == 400
