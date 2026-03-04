import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.agent.pricing_agent import analyze_property

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pricing", tags=["pricing-agent"])


class AnalyzeRequest(BaseModel):
    property_id: str


@router.post("/analyze")
async def analyze(body: AnalyzeRequest, request: Request):
    """Invoke the Pricing Strategy Agent for a property.

    The agent will:
    1. Fetch property details from the Property Listing service
    2. Find comparable sales from the Market Data service
    3. Get market statistics
    4. Reason about pricing (via LLM or mock fallback)
    5. Return a validated pricing recommendation
    """
    result = await analyze_property(
        property_id=body.property_id,
        llm_client=request.app.state.llm_client,
        model=request.app.state.llm_model,
        tool_executor=request.app.state.tool_executor,
    )
    return result
