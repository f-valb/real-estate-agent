"""Home Finder Agent — FastAPI application."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from openai import AsyncOpenAI

from app.agent.tools import ToolExecutor
from app.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    property_url = os.getenv("PROPERTY_SERVICE_URL", "http://property-listing:8000")
    litellm_url = os.getenv("LITELLM_URL", "http://litellm:4000/v1")
    llm_model = os.getenv("LLM_MODEL", "qwen2.5:14b")

    logger.info("Home Finder starting — property_url=%s, llm=%s", property_url, llm_model)

    app.state.tool_executor = ToolExecutor(property_service_url=property_url)
    app.state.llm_model = llm_model
    app.state.llm_client = AsyncOpenAI(
        base_url=litellm_url,
        api_key="sk-litellm-dev-key",
    )

    yield

    await app.state.tool_executor.close()
    logger.info("Home Finder shutdown complete")


app = FastAPI(title="Home Finder Agent", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "home-finder"}
