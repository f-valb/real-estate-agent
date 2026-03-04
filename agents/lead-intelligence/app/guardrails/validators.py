"""Output validation and guardrails for lead assessments."""
import logging

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"call", "email", "send_listings", "schedule_showing", "refer_to_lender", "nurture", "archive"}
VALID_QUALIFICATIONS = {"hot", "warm", "cold"}
VALID_TIMELINES = {"0-3 months", "3-6 months", "6-12 months", "12+ months", "unknown"}


class LeadAssessment(BaseModel):
    lead_score: int = Field(..., ge=0, le=100)
    qualification: str
    buying_timeline: str
    recommended_actions: list[str] = Field(..., min_length=1)
    reasoning: str = Field(..., min_length=10)
    matching_listing_count: int = Field(default=0, ge=0)

    @field_validator("qualification", mode="before")
    @classmethod
    def validate_qualification(cls, v):
        v = str(v).lower().strip()
        if v not in VALID_QUALIFICATIONS:
            return "cold"
        return v

    @field_validator("buying_timeline", mode="before")
    @classmethod
    def validate_timeline(cls, v):
        v = str(v).lower().strip()
        if v not in VALID_TIMELINES:
            return "unknown"
        return v

    @field_validator("recommended_actions", mode="before")
    @classmethod
    def validate_actions(cls, v):
        if isinstance(v, list):
            filtered = [a for a in v if a in VALID_ACTIONS]
            return filtered if filtered else ["nurture"]
        return ["nurture"]


def validate_assessment(data: dict) -> LeadAssessment:
    """Validate and sanitize a lead assessment from the agent."""
    score = data.get("lead_score", 0)

    # Ensure qualification matches score
    if score >= 70:
        data["qualification"] = "hot"
    elif score >= 40:
        data["qualification"] = "warm"
    else:
        data["qualification"] = "cold"

    assessment = LeadAssessment(**data)
    logger.info(
        "Validated lead assessment: score=%d, qualification=%s, actions=%s",
        assessment.lead_score,
        assessment.qualification,
        assessment.recommended_actions,
    )
    return assessment
