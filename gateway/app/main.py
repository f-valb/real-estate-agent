import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import properties, contacts, market, agents

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | gateway | %(levelname)s | %(message)s")

    app.state.http_client = httpx.AsyncClient(timeout=60.0)
    app.state.config = {
        "PROPERTY_SERVICE_URL": os.getenv("PROPERTY_SERVICE_URL", "http://property-listing:8000"),
        "CRM_SERVICE_URL": os.getenv("CRM_SERVICE_URL", "http://crm-contact:8000"),
        "MARKET_SERVICE_URL": os.getenv("MARKET_SERVICE_URL", "http://market-data:8000"),
        "PRICING_AGENT_URL": os.getenv("PRICING_AGENT_URL", "http://pricing-strategy:8000"),
        "LEAD_AGENT_URL": os.getenv("LEAD_AGENT_URL", "http://lead-intelligence:8000"),
        "HOME_FINDER_URL": os.getenv("HOME_FINDER_URL", "http://home-finder:8000"),
    }

    logger.info("Gateway started with service URLs: %s", app.state.config)
    yield

    await app.state.http_client.aclose()


app = FastAPI(title="Real Estate Agent - API Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties.router)
app.include_router(contacts.router)
app.include_router(market.router)
app.include_router(agents.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}
