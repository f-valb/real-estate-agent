import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from openai import AsyncOpenAI

from app.agent.tools import ToolExecutor
from app.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | lead-intelligence | %(levelname)s | %(name)s | %(message)s",
    )

    litellm_url = os.getenv("LITELLM_URL", "http://litellm:4000/v1")
    model = os.getenv("LLM_MODEL", "qwen2.5:14b")

    app.state.llm_client = AsyncOpenAI(
        base_url=litellm_url,
        api_key="sk-litellm-dev-key",
    )
    app.state.llm_model = model

    app.state.tool_executor = ToolExecutor(
        crm_service_url=os.getenv("CRM_SERVICE_URL", "http://crm-contact:8000"),
        property_service_url=os.getenv("PROPERTY_SERVICE_URL", "http://property-listing:8000"),
        market_service_url=os.getenv("MARKET_SERVICE_URL", "http://market-data:8000"),
    )

    logger.info("Lead Intelligence Agent started (model=%s, litellm=%s)", model, litellm_url)
    yield

    await app.state.tool_executor.close()


app = FastAPI(title="Lead Intelligence Agent", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "lead-intelligence"}
