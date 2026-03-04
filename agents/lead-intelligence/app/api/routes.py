import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.agent.lead_agent import score_lead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/leads", tags=["lead-intelligence"])


class ScoreRequest(BaseModel):
    contact_id: str


@router.post("/score")
async def score(body: ScoreRequest, request: Request):
    """Invoke the Lead Intelligence Agent for a contact.

    The agent will:
    1. Fetch contact details from the CRM service
    2. Get interaction history
    3. Find matching listings based on preferences
    4. Check market conditions
    5. Score the lead and recommend actions
    """
    result = await score_lead(
        contact_id=body.contact_id,
        llm_client=request.app.state.llm_client,
        model=request.app.state.llm_model,
        tool_executor=request.app.state.tool_executor,
    )
    return result
