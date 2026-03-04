"""Core agent loop for the Lead Intelligence Agent.

Uses OpenAI SDK pointed at LiteLLM -> Ollama/Qwen.
Falls back to heuristic-based scoring when LLM is unavailable.
"""
import json
import logging

from openai import AsyncOpenAI, APIConnectionError

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from app.guardrails.validators import LeadAssessment, validate_assessment

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 6

VALID_ACTIONS = {"call", "email", "send_listings", "schedule_showing", "refer_to_lender", "nurture", "archive"}


async def score_lead(
    contact_id: str,
    llm_client: AsyncOpenAI,
    model: str,
    tool_executor: ToolExecutor,
) -> dict:
    """Run the lead intelligence agent for a given contact."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Assess contact {contact_id} and provide a lead score with recommended actions."},
    ]

    try:
        return await _agent_loop(messages, llm_client, model, tool_executor)
    except (APIConnectionError, Exception) as e:
        logger.warning("LLM unavailable (%s), falling back to heuristic scoring", e)
        return await _heuristic_scoring(contact_id, tool_executor)


async def _agent_loop(
    messages: list[dict],
    client: AsyncOpenAI,
    model: str,
    tool_executor: ToolExecutor,
) -> dict:
    for iteration in range(MAX_ITERATIONS):
        logger.info("Lead agent iteration %d/%d", iteration + 1, MAX_ITERATIONS)

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=2048,
        )

        choice = response.choices[0]
        message = choice.message

        if message.tool_calls:
            messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                logger.info("Tool call: %s(%s)", fn_name, fn_args)

                result = await tool_executor.execute(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            continue

        if message.content:
            assessment = _extract_assessment(message.content)
            validated = validate_assessment(assessment)
            return validated.model_dump()

    raise RuntimeError("Lead agent exceeded maximum iterations")


def _extract_assessment(content: str) -> dict:
    content = content.strip()

    if "```json" in content:
        start = content.index("```json") + 7
        end = content.index("```", start)
        content = content[start:end].strip()
    elif "```" in content:
        start = content.index("```") + 3
        end = content.index("```", start)
        content = content[start:end].strip()

    if "{" in content:
        start = content.index("{")
        depth = 0
        for i in range(start, len(content)):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    content = content[start:i + 1]
                    break

    return json.loads(content)


async def _heuristic_scoring(contact_id: str, tool_executor: ToolExecutor) -> dict:
    """Score a lead using simple heuristics when LLM is unavailable."""
    logger.info("Running heuristic scoring for contact %s", contact_id)

    # Fetch contact
    contact_data = json.loads(await tool_executor.execute("get_contact_details", {"contact_id": contact_id}))
    if "error" in contact_data:
        raise RuntimeError(f"Cannot fetch contact: {contact_data['error']}")

    # Fetch interactions
    interactions_data = json.loads(
        await tool_executor.execute("get_interaction_history", {"contact_id": contact_id, "limit": 50})
    )
    interactions = interactions_data if isinstance(interactions_data, list) else []

    # Fetch matching listings
    preferences = contact_data.get("preferences") or {}
    listing_count = 0
    if preferences:
        listing_args = {}
        if "min_price" in preferences:
            listing_args["min_price"] = preferences["min_price"]
        if "max_price" in preferences:
            listing_args["max_price"] = preferences["max_price"]
        if "bedrooms" in preferences:
            listing_args["bedrooms"] = preferences["bedrooms"]
        areas = preferences.get("preferred_areas", [])
        if areas:
            listing_args["city"] = areas[0]

        listings_data = json.loads(await tool_executor.execute("get_matching_listings", listing_args))
        listing_count = listings_data.get("total", 0) if isinstance(listings_data, dict) else 0

    # Heuristic scoring
    score = 0

    # Contact completeness (0-15)
    if contact_data.get("email"):
        score += 5
    if contact_data.get("phone"):
        score += 5
    if preferences:
        score += 5

    # Engagement (0-25)
    interaction_count = len(interactions)
    if interaction_count > 10:
        score += 25
    elif interaction_count > 5:
        score += 20
    elif interaction_count > 2:
        score += 15
    elif interaction_count > 0:
        score += 8

    # Pipeline stage (0-25)
    stage = contact_data.get("pipeline_stage", "new")
    stage_scores = {"new": 5, "contacted": 10, "qualified": 18, "proposal": 22, "negotiation": 25}
    score += stage_scores.get(stage, 0)

    # Market alignment (0-20)
    if listing_count > 10:
        score += 20
    elif listing_count > 5:
        score += 15
    elif listing_count > 0:
        score += 10

    # Lead source (0-15)
    source = contact_data.get("lead_source", "")
    source_scores = {"referral": 15, "open_house": 12, "website": 10, "realtor.com": 8, "zillow": 8, "social_media": 5}
    score += source_scores.get(source, 3)

    score = min(score, 100)

    # Qualification
    if score >= 70:
        qualification = "hot"
    elif score >= 40:
        qualification = "warm"
    else:
        qualification = "cold"

    # Cap score if no interactions
    if interaction_count == 0:
        score = min(score, 30)
        qualification = "cold" if score < 40 else qualification

    # Recommended actions
    actions = []
    if qualification == "hot":
        actions = ["call", "schedule_showing"]
    elif qualification == "warm":
        actions = ["email", "send_listings"]
    else:
        actions = ["nurture"]

    if listing_count > 0 and "send_listings" not in actions:
        actions.append("send_listings")

    # Timeline
    timeline_map = {"negotiation": "0-3 months", "proposal": "0-3 months", "qualified": "3-6 months",
                    "contacted": "6-12 months", "new": "unknown"}
    timeline = timeline_map.get(stage, "unknown")

    result = {
        "lead_score": score,
        "qualification": qualification,
        "buying_timeline": timeline,
        "recommended_actions": actions,
        "reasoning": (
            f"Contact {contact_data.get('first_name', '')} {contact_data.get('last_name', '')} "
            f"is a {contact_data.get('contact_type', 'lead')} in '{stage}' stage with "
            f"{interaction_count} interactions. {listing_count} matching listings available. "
            f"(Heuristic scoring - LLM unavailable)"
        ),
        "matching_listing_count": listing_count,
    }

    validated = validate_assessment(result)
    return validated.model_dump()
