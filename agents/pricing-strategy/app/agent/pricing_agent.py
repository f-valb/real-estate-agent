"""Core agent loop for the Pricing Strategy Agent.

Uses the OpenAI SDK pointed at LiteLLM (which routes to Ollama/Qwen).
Implements the ReAct pattern: reason -> tool call -> observe -> repeat.
Falls back to mock responses when LLM is unavailable.
"""
import json
import logging
import statistics

from openai import AsyncOpenAI, APIConnectionError

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from app.guardrails.validators import PricingRecommendation, validate_recommendation

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5


async def analyze_property(
    property_id: str,
    llm_client: AsyncOpenAI,
    model: str,
    tool_executor: ToolExecutor,
) -> dict:
    """Run the pricing agent loop for a given property.

    Returns a validated PricingRecommendation dict.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze property {property_id} and recommend a listing price. Use the tools to gather data first."},
    ]

    try:
        return await _agent_loop(messages, llm_client, model, tool_executor)
    except (APIConnectionError, Exception) as e:
        logger.warning("LLM unavailable (%s), falling back to mock analysis", e)
        return await _mock_analysis(property_id, tool_executor)


async def _agent_loop(
    messages: list[dict],
    client: AsyncOpenAI,
    model: str,
    tool_executor: ToolExecutor,
) -> dict:
    """Execute the agent reasoning loop with tool calls."""
    for iteration in range(MAX_ITERATIONS):
        logger.info("Agent iteration %d/%d", iteration + 1, MAX_ITERATIONS)

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=4096,
        )

        choice = response.choices[0]
        message = choice.message

        # If the model wants to call tools
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

        # Model finished reasoning — extract recommendation
        if message.content:
            recommendation = _extract_recommendation(message.content)
            validated = validate_recommendation(recommendation)
            return validated.model_dump()

    raise RuntimeError("Agent exceeded maximum iterations without producing a result")


def _extract_recommendation(content: str) -> dict:
    """Extract JSON recommendation from the LLM's text response."""
    # Try to find JSON block in the response
    content = content.strip()

    # Look for JSON in code blocks
    if "```json" in content:
        start = content.index("```json") + 7
        end = content.index("```", start)
        content = content[start:end].strip()
    elif "```" in content:
        start = content.index("```") + 3
        end = content.index("```", start)
        content = content[start:end].strip()

    # Try to find JSON object
    if "{" in content:
        start = content.index("{")
        # Find matching closing brace
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


async def _mock_analysis(property_id: str, tool_executor: ToolExecutor) -> dict:
    """Generate a data-driven mock analysis when LLM is unavailable.

    Still calls the microservice APIs for real data, just skips the LLM reasoning.
    """
    logger.info("Running mock analysis for property %s", property_id)

    # Fetch property details
    prop_data = json.loads(await tool_executor.execute("get_property_details", {"property_id": property_id}))
    if "error" in prop_data:
        raise RuntimeError(f"Cannot fetch property: {prop_data['error']}")

    zip_code = prop_data.get("zip_code", "00000")
    bedrooms = prop_data.get("bedrooms")
    sqft = prop_data.get("square_feet")

    # Fetch comps
    comp_args = {"zip_code": zip_code, "limit": 10}
    if bedrooms:
        comp_args["bedrooms"] = bedrooms
    if sqft:
        comp_args["sqft_min"] = int(sqft * 0.8)
        comp_args["sqft_max"] = int(sqft * 1.2)

    comps_data = json.loads(await tool_executor.execute("get_comparable_sales", comp_args))
    comps = comps_data if isinstance(comps_data, list) else []

    # Fetch market stats
    stats_data = json.loads(await tool_executor.execute("get_market_stats", {"zip_code": zip_code}))

    # Compute recommendation from comps
    comp_prices = [float(c["sale_price"]) for c in comps if c.get("sale_price")]

    if comp_prices:
        median = statistics.median(comp_prices)
        recommended = int(median)
        price_range = int(median * 0.05)
    else:
        # Fall back to list price
        recommended = int(float(prop_data.get("list_price", 350000)))
        price_range = int(recommended * 0.05)

    confidence = "high" if len(comp_prices) >= 5 else "medium" if len(comp_prices) >= 3 else "low"
    comps_used = [c.get("mls_number", "unknown") for c in comps[:5] if c.get("mls_number")]

    result = {
        "recommended_price": recommended,
        "price_range_low": recommended - price_range,
        "price_range_high": recommended + price_range,
        "confidence": confidence,
        "justification": (
            f"Based on {len(comp_prices)} comparable sales in {zip_code}, "
            f"the median sale price is ${median:,.0f}. "
            f"This property has {bedrooms or 'N/A'} bedrooms and {sqft or 'N/A'} sqft. "
            f"(Mock analysis - LLM unavailable)"
        ) if comp_prices else (
            f"No comparable sales found in {zip_code}. Using list price as baseline. "
            f"(Mock analysis - LLM unavailable)"
        ),
        "comps_used": comps_used,
        "market_context": {
            "median_price": float(stats_data.get("median_price", 0)) if stats_data and not isinstance(stats_data, str) else None,
            "avg_dom": stats_data.get("median_dom") if stats_data and not isinstance(stats_data, str) else None,
            "total_comps_found": len(comps),
        },
    }

    validated = validate_recommendation(result)
    return validated.model_dump()
