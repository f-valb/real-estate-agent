"""Output validation for the Home Finder agent."""
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExtractedCriteria(BaseModel):
    location: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    min_bedrooms: int | None = None
    property_type: str | None = None
    priorities: list[str] = Field(default_factory=list)


class HomefinderResult(BaseModel):
    buyer_intent: str = Field(..., min_length=5)
    extracted_criteria: ExtractedCriteria = Field(default_factory=ExtractedCriteria)
    match_reasoning: str = Field(..., min_length=10)
    matched_listing_ids: list[str] = Field(default_factory=list)
    total_found: int = Field(default=0, ge=0)
    matched_listings: list[dict] = Field(default_factory=list)
    search_params_used: dict = Field(default_factory=dict)


def validate_result(data: dict) -> HomefinderResult:
    """Validate and clean the agent output."""
    # Ensure matched_listing_ids is a list of strings
    ids = data.get("matched_listing_ids", [])
    if isinstance(ids, str):
        ids = [ids]
    data["matched_listing_ids"] = [str(i) for i in ids]

    # Ensure total_found is consistent
    data["total_found"] = len(data["matched_listing_ids"])

    try:
        result = HomefinderResult(**data)
    except Exception as e:
        logger.warning("Validation error, applying defaults: %s", e)
        result = HomefinderResult(
            buyer_intent=data.get("buyer_intent", "Home search based on your description"),
            match_reasoning=data.get("match_reasoning", "Searched available listings matching your criteria."),
            matched_listing_ids=data.get("matched_listing_ids", []),
            total_found=len(data.get("matched_listing_ids", [])),
            matched_listings=data.get("matched_listings", []),
            search_params_used=data.get("search_params_used", {}),
        )

    logger.info(
        "HomefinderResult validated: %d matches, intent=%r",
        result.total_found,
        result.buyer_intent[:60],
    )
    return result
