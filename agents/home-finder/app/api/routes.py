"""API routes for the Home Finder agent."""
import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.agent.home_finder_agent import find_homes, chat_step

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchRequest(BaseModel):
    description: str


class ChatMessageIn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessageIn]


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


@router.post("/api/v1/home-finder/chat")
async def chat_home(body: ChatRequest, request: Request):
    """Conversational home-finder: one turn of guided Q&A or a search trigger."""
    if not body.messages:
        raise HTTPException(status_code=422, detail="messages must not be empty")

    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    logger.info("Home finder chat: %d message(s) in history", len(messages))
    try:
        return await chat_step(
            messages=messages,
            llm_client=request.app.state.llm_client,
            tool_executor=request.app.state.tool_executor,
            llm_model=request.app.state.llm_model,
        )
    except Exception as e:
        logger.error("Home finder chat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
