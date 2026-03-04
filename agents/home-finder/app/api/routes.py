"""API routes for the Home Finder agent."""
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.agent.home_finder_agent import find_homes

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchRequest(BaseModel):
    description: str


@router.post("/api/v1/home-finder/search")
async def search_homes(req: SearchRequest, request: Request):
    """Find listings matching a natural language buyer description."""
    if not req.description or len(req.description.strip()) < 5:
        raise HTTPException(status_code=422, detail="Description must be at least 5 characters")

    logger.info("Home finder search: %r", req.description[:100])
    try:
        result = await find_homes(
            description=req.description,
            llm_client=request.app.state.llm_client,
            tool_executor=request.app.state.tool_executor,
            llm_model=request.app.state.llm_model,
        )
        return result.model_dump()
    except Exception as e:
        logger.error("Home finder error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
