"""Integration tests for the Lead Intelligence Agent."""
import pytest
import httpx

CRM_URL = "http://localhost:8001"
LEAD_URL = "http://localhost:8011"
GATEWAY_URL = "http://localhost:8090"


@pytest.fixture
async def client():
    async with httpx.AsyncClient(timeout=120.0) as c:
        yield c


@pytest.mark.asyncio
async def test_lead_agent_health(client):
    resp = await client.get(f"{LEAD_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_lead_scoring(client):
    """Test the full lead scoring flow."""
    # Get a contact to score
    resp = await client.get(f"{CRM_URL}/api/v1/contacts", params={"limit": 1})
    assert resp.status_code == 200
    contacts = resp.json()

    if contacts["total"] == 0:
        pytest.skip("No contacts. Run `make seed` first.")

    contact_id = contacts["items"][0]["id"]

    # Score via lead agent
    resp = await client.post(
        f"{LEAD_URL}/api/v1/leads/score",
        json={"contact_id": contact_id},
    )
    assert resp.status_code == 200
    result = resp.json()

    # Validate response structure
    assert "lead_score" in result
    assert "qualification" in result
    assert "buying_timeline" in result
    assert "recommended_actions" in result
    assert "reasoning" in result

    assert 0 <= result["lead_score"] <= 100
    assert result["qualification"] in ("hot", "warm", "cold")
    assert result["buying_timeline"] in ("0-3 months", "3-6 months", "6-12 months", "12+ months", "unknown")
    assert len(result["recommended_actions"]) >= 1
    assert len(result["reasoning"]) > 10


@pytest.mark.asyncio
async def test_lead_scoring_via_gateway(client):
    """Test lead scoring through the API gateway."""
    resp = await client.get(f"{CRM_URL}/api/v1/contacts", params={"limit": 1})
    if resp.json()["total"] == 0:
        pytest.skip("No contacts. Run `make seed` first.")

    contact_id = resp.json()["items"][0]["id"]

    resp = await client.post(
        f"{GATEWAY_URL}/api/v1/agents/leads/score",
        json={"contact_id": contact_id},
    )
    assert resp.status_code == 200
    assert "lead_score" in resp.json()
