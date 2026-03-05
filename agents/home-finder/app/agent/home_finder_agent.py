"""Home Finder agent — matches buyer descriptions to listings using LLM + tools."""
from __future__ import annotations

import json
import logging
import re

from openai import AsyncOpenAI, APIConnectionError

from app.agent.prompts import SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT
from app.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from app.guardrails.validators import HomefinderResult, validate_result

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 6


async def find_homes(
    description: str,
    llm_client: AsyncOpenAI,
    tool_executor: ToolExecutor,
    llm_model: str,
) -> HomefinderResult:
    """Main entry point: parse description, search listings, return ranked results."""
    try:
        result_data = await _agent_loop(description, llm_client, tool_executor, llm_model)
    except (APIConnectionError, Exception) as e:
        logger.warning("LLM unavailable (%s), using heuristic fallback", e)
        result_data = await _heuristic_search(description, tool_executor)

    # Fetch full listing objects for all matched IDs
    result_data = await _attach_listings(result_data, tool_executor)
    return validate_result(result_data)


async def _agent_loop(
    description: str,
    llm_client: AsyncOpenAI,
    tool_executor: ToolExecutor,
    llm_model: str,
) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Please find matching listings for this buyer description:\n\n"
                f'"{description}"\n\n'
                "Search the listings database and return your analysis as JSON."
            ),
        },
    ]

    for iteration in range(MAX_ITERATIONS):
        logger.info("Agent iteration %d/%d", iteration + 1, MAX_ITERATIONS)
        response = await llm_client.chat.completions.create(
            model=llm_model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=4096,
            temperature=0.2,
        )
        message = response.choices[0].message

        # Tool calls
        if message.tool_calls:
            messages.append(message)
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                logger.info("Calling tool: %s(%s)", tc.function.name, args)
                result = await tool_executor.execute(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            continue

        # Final response
        content = message.content or ""
        logger.debug("Agent final response: %s", content[:200])
        return _extract_json(content)

    raise RuntimeError("Agent exceeded max iterations without producing output")


def _extract_json(text: str) -> dict:
    """Extract the JSON object from LLM output (handles code fences)."""
    # Try code block first
    block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if block:
        return json.loads(block.group(1))
    # Try bare JSON object
    obj = re.search(r"\{.*\}", text, re.DOTALL)
    if obj:
        return json.loads(obj.group(0))
    raise ValueError(f"No JSON found in response: {text[:300]}")


async def _heuristic_search(description: str, tool_executor: ToolExecutor) -> dict:
    """Fallback: parse description with regex and call search tool directly."""
    desc_lower = description.lower()
    params: dict = {}

    # Extract city
    cities = ["austin", "dallas", "houston", "san antonio"]
    for city in cities:
        if city in desc_lower:
            params["city"] = city.title()
            break

    # Extract bedrooms
    bed_match = re.search(r"(\d+)\s*(?:\+\s*)?(?:bed|bedroom|br)\b", desc_lower)
    if bed_match:
        params["bedrooms"] = int(bed_match.group(1))

    # Extract price — handles "$500k", "500,000", "$500,000", "half a million"
    price_match = re.search(r"\$?([\d,]+)\s*k\b", desc_lower)
    if price_match:
        val = int(price_match.group(1).replace(",", "")) * 1000
        params["min_price"] = int(val * 0.8)
        params["max_price"] = int(val * 1.2)
    else:
        price_match = re.search(r"\$?([\d,]{3,})", desc_lower)
        if price_match:
            val = int(price_match.group(1).replace(",", ""))
            if val > 10000:
                params["min_price"] = int(val * 0.8)
                params["max_price"] = int(val * 1.2)

    # Extract priorities from keywords
    priorities = []
    keyword_map = {
        "yard": ["yard", "garden", "outdoor space", "backyard"],
        "downtown": ["downtown", "city centre", "urban"],
        "quiet": ["quiet", "peaceful", "calm"],
        "school": ["school", "district"],
        "garage": ["garage"],
        "new construction": ["new construction", "newly built", "brand new"],
        "pool": ["pool"],
        "open floor plan": ["open floor", "open plan", "open concept"],
    }
    for priority, kws in keyword_map.items():
        if any(kw in desc_lower for kw in kws):
            priorities.append(priority)

    params["limit"] = 20
    logger.info("Heuristic search params: %s", params)

    raw = await tool_executor.execute("search_listings", params)
    data = json.loads(raw)
    items = data.get("items", [])

    # Build criteria summary
    location = params.get("city") or params.get("zip_code") or "any location"
    price_str = ""
    if "min_price" in params and "max_price" in params:
        price_str = f"${params['min_price']//1000}k–${params['max_price']//1000}k"
    bed_str = f"{params['bedrooms']}+ bedrooms" if "bedrooms" in params else "any bedroom count"

    intent_parts = []
    if location != "any location":
        intent_parts.append(f"in {location}")
    if price_str:
        intent_parts.append(f"priced {price_str}")
    if "bedrooms" in params:
        intent_parts.append(bed_str)

    buyer_intent = f"Buyer is looking for a home {', '.join(intent_parts) if intent_parts else 'matching their description'}."

    matched_ids = [item["id"] for item in items[:8]]
    reasoning = (
        f"Based on your description, I extracted the following search criteria: "
        f"location={location}, {bed_str}, price range={price_str or 'any'}. "
        f"Found {len(items)} matching active listings."
        " (Note: Running in heuristic mode — LLM unavailable.)"
    )

    return {
        "buyer_intent": buyer_intent,
        "extracted_criteria": {
            "location": params.get("city") or params.get("zip_code"),
            "min_price": params.get("min_price"),
            "max_price": params.get("max_price"),
            "min_bedrooms": params.get("bedrooms"),
            "property_type": None,
            "priorities": priorities,
        },
        "match_reasoning": reasoning,
        "matched_listing_ids": matched_ids,
        "total_found": len(matched_ids),
        "search_params_used": params,
    }


GUIDED_QUESTIONS = [
    "Where are you hoping to live? Any particular city, neighbourhood, or area in mind?",
    "What's your rough budget? For example, 'under $500k' or 'around $400–600k'.",
    "How many bedrooms do you need? And do you have any must-haves — like a yard, garage, or home office?",
    "Are you thinking house, condo, or townhouse? Any other priorities — good schools, short commute, quiet street?",
]


async def chat_step(
    messages: list[dict],
    llm_client: AsyncOpenAI,
    tool_executor: ToolExecutor,
    llm_model: str,
) -> dict:
    """One conversational turn: either ask a follow-up question or trigger a search.

    Returns one of:
      {"action": "question", "thought": str, "question": str}
      {"action": "results",  "thought": str, "result": dict}
    """
    try:
        llm_messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + messages
        response = await llm_client.chat.completions.create(
            model=llm_model,
            messages=llm_messages,
            max_tokens=1024,
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        logger.debug("Chat LLM response: %s", content[:300])
        parsed = _extract_json(content)

        if parsed.get("action") == "search":
            description = (
                parsed.get("search_params", {}).get("description")
                or " ".join(m["content"] for m in messages if m["role"] == "user")
            )
            thought = parsed.get("thought", "")
            logger.info("Chat agent triggering search: %r", description[:100])
            result = await find_homes(description, llm_client, tool_executor, llm_model)
            return {"action": "results", "thought": thought, "result": result.model_dump()}

        # action == "question"
        return {
            "action": "question",
            "thought": parsed.get("thought", ""),
            "question": parsed.get("question", "Could you tell me more about what you're looking for?"),
        }

    except Exception as e:
        logger.warning("Chat LLM step failed (%s), using heuristic", e)
        return await _heuristic_chat_step(messages, tool_executor)


async def _heuristic_chat_step(messages: list[dict], tool_executor: ToolExecutor) -> dict:
    """Fallback guided questions when LLM is unavailable."""
    user_msgs = [m for m in messages if m["role"] == "user"]
    n = len(user_msgs)

    if n < len(GUIDED_QUESTIONS):
        question = GUIDED_QUESTIONS[n]
        return {
            "action": "question",
            "thought": f"Gathering context (exchange {n + 1} of {len(GUIDED_QUESTIONS)}). "
                       f"Asked about: {['location', 'budget', 'bedrooms', 'type/lifestyle'][:n]}. "
                       f"Now asking about {['location', 'budget', 'bedrooms', 'type/lifestyle'][n]}.",
            "question": question,
        }

    # Enough context — build description from all user messages and search
    combined = " ".join(m["content"] for m in user_msgs)
    logger.info("Heuristic chat: enough context after %d exchanges, searching", n)
    result_data = await _heuristic_search(combined, tool_executor)
    result_data = await _attach_listings(result_data, tool_executor)
    validated = validate_result(result_data)
    return {
        "action": "results",
        "thought": f"Collected information across {n} exchanges. "
                   f"Searching with combined description: {combined[:120]}...",
        "result": validated.model_dump(),
    }


async def _attach_listings(result_data: dict, tool_executor: ToolExecutor) -> dict:
    """Fetch full PropertyResponse objects for all matched listing IDs."""
    ids = result_data.get("matched_listing_ids", [])
    if not ids:
        result_data["matched_listings"] = []
        return result_data

    listings = []
    for listing_id in ids:
        try:
            raw = await tool_executor.execute("get_listing_details", {"property_id": listing_id})
            listing = json.loads(raw)
            if "error" not in listing:
                listings.append(listing)
        except Exception as e:
            logger.warning("Failed to fetch listing %s: %s", listing_id, e)

    result_data["matched_listings"] = listings
    result_data["total_found"] = len(listings)
    return result_data
