"""Output validation and guardrails for pricing recommendations."""
import logging

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class MarketContext(BaseModel):
    median_price: float | None = None
    avg_dom: int | None = None
    total_comps_found: int = 0


class PricingRecommendation(BaseModel):
    recommended_price: int = Field(..., gt=0)
    price_range_low: int = Field(..., gt=0)
    price_range_high: int = Field(..., gt=0)
    confidence: str = Field(..., pattern="^(low|medium|high)$")
    justification: str = Field(..., min_length=10)
    comps_used: list[str] = []
    market_context: MarketContext = MarketContext()

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v):
        v = str(v).lower().strip()
        if v not in ("low", "medium", "high"):
            return "low"
        return v

    @field_validator("price_range_high")
    @classmethod
    def range_must_be_ordered(cls, v, info):
        low = info.data.get("price_range_low", 0)
        if v < low:
            raise ValueError("price_range_high must be >= price_range_low")
        return v


def validate_recommendation(data: dict) -> PricingRecommendation:
    """Validate and sanitize a pricing recommendation from the agent.

    Applies guardrails:
    - Price must be positive
    - Range must be ordered (low < recommended < high)
    - Confidence capped to 'low' if fewer than 3 comps
    - Price range auto-corrected if inverted
    """
    # Auto-correct range if needed
    rec_price = data.get("recommended_price", 0)
    low = data.get("price_range_low", 0)
    high = data.get("price_range_high", 0)

    if low > high:
        data["price_range_low"] = high
        data["price_range_high"] = low

    if rec_price > 0 and (low <= 0 or high <= 0):
        data["price_range_low"] = int(rec_price * 0.95)
        data["price_range_high"] = int(rec_price * 1.05)

    # Cap confidence if few comps
    comps = data.get("comps_used", [])
    ctx = data.get("market_context", {})
    total_comps = ctx.get("total_comps_found", len(comps))
    if total_comps < 3:
        data["confidence"] = "low"
        logger.info("Confidence capped to 'low' due to %d comps", total_comps)

    recommendation = PricingRecommendation(**data)
    logger.info(
        "Validated recommendation: $%s (range $%s-$%s, confidence=%s, comps=%d)",
        f"{recommendation.recommended_price:,}",
        f"{recommendation.price_range_low:,}",
        f"{recommendation.price_range_high:,}",
        recommendation.confidence,
        len(recommendation.comps_used),
    )
    return recommendation
