"""Shared fixtures for integration tests.

These tests run against the live services via Docker Compose.
Run `make up` and `make seed` before running tests.
"""
import pytest
import httpx

GATEWAY_URL = "http://localhost:8090"
PROPERTY_URL = "http://localhost:8000"
CRM_URL = "http://localhost:8001"
MARKET_URL = "http://localhost:8002"
PRICING_AGENT_URL = "http://localhost:8010"
LEAD_AGENT_URL = "http://localhost:8011"


@pytest.fixture
def gateway_url():
    return GATEWAY_URL


@pytest.fixture
async def client():
    async with httpx.AsyncClient(timeout=60.0) as c:
        yield c
