"""Proxy routes for AI Agent services."""
import logging

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


async def _proxy_agent(request: Request, service_key: str, path: str) -> Response:
    client = request.app.state.http_client
    url = f"{request.app.state.config[service_key]}{path}"

    body = await request.body()
    try:
        resp = await client.request(
            method=request.method,
            url=url,
            content=body if body else None,
            headers={"content-type": "application/json"},
            timeout=120.0,  # agents may take longer due to LLM calls
        )
        return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
    except Exception as e:
        logger.error("Agent service error (%s): %s", service_key, e)
        return Response(
            content=f'{{"detail": "Agent service unavailable: {e}"}}',
            status_code=503,
            media_type="application/json",
        )


@router.post("/pricing/analyze")
async def pricing_analyze(request: Request):
    return await _proxy_agent(request, "PRICING_AGENT_URL", "/api/v1/pricing/analyze")


@router.post("/leads/score")
async def lead_score(request: Request):
    return await _proxy_agent(request, "LEAD_AGENT_URL", "/api/v1/leads/score")


@router.post("/home-finder/search")
async def home_finder_search(request: Request):
    return await _proxy_agent(request, "HOME_FINDER_URL", "/api/v1/home-finder/search")
