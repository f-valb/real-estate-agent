"""Tool definitions and execution for the Pricing Strategy Agent.

Tools follow OpenAI function-calling format and are dispatched to
microservice APIs via httpx.
"""
import json
import logging

import httpx

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_property_details",
            "description": "Retrieve full details of a property listing by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "UUID of the property listing",
                    }
                },
                "required": ["property_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_comparable_sales",
            "description": "Find comparable recent sales in the same area. Returns sales data sorted by most recent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zip_code": {"type": "string", "description": "ZIP code to search in"},
                    "bedrooms": {"type": "integer", "description": "Number of bedrooms to match"},
                    "sqft_min": {"type": "integer", "description": "Minimum square footage"},
                    "sqft_max": {"type": "integer", "description": "Maximum square footage"},
                    "limit": {"type": "integer", "description": "Max results to return", "default": 10},
                },
                "required": ["zip_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_stats",
            "description": "Get current market statistics for a ZIP code (median price, avg DOM, inventory).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zip_code": {"type": "string", "description": "ZIP code to get stats for"},
                },
                "required": ["zip_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_trends",
            "description": "Get monthly average price trends for a ZIP code over the last N months.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zip_code": {"type": "string", "description": "ZIP code"},
                    "months": {"type": "integer", "description": "Number of months of history", "default": 12},
                },
                "required": ["zip_code"],
            },
        },
    },
]


class ToolExecutor:
    """Executes tool calls by dispatching to microservice REST APIs."""

    def __init__(self, property_service_url: str, market_service_url: str):
        self._property_url = property_service_url
        self._market_url = market_service_url
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    async def execute(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool and return JSON string result."""
        try:
            if tool_name == "get_property_details":
                return await self._get_property_details(arguments["property_id"])
            elif tool_name == "get_comparable_sales":
                return await self._get_comparable_sales(arguments)
            elif tool_name == "get_market_stats":
                return await self._get_market_stats(arguments["zip_code"])
            elif tool_name == "get_price_trends":
                return await self._get_price_trends(
                    arguments["zip_code"],
                    arguments.get("months", 12),
                )
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        except httpx.ConnectError as e:
            logger.error("Service connection error for %s: %s", tool_name, e)
            return json.dumps({"error": f"Service unavailable: {e}"})
        except Exception as e:
            logger.error("Tool execution error for %s: %s", tool_name, e)
            return json.dumps({"error": str(e)})

    async def _get_property_details(self, property_id: str) -> str:
        resp = await self._client.get(f"{self._property_url}/api/v1/listings/{property_id}")
        resp.raise_for_status()
        return json.dumps(resp.json())

    async def _get_comparable_sales(self, args: dict) -> str:
        params = {"zip_code": args["zip_code"]}
        if "bedrooms" in args:
            params["bedrooms"] = args["bedrooms"]
        if "sqft_min" in args:
            params["sqft_min"] = args["sqft_min"]
        if "sqft_max" in args:
            params["sqft_max"] = args["sqft_max"]
        if "limit" in args:
            params["limit"] = args["limit"]

        resp = await self._client.get(f"{self._market_url}/api/v1/market/comps", params=params)
        resp.raise_for_status()
        return json.dumps(resp.json())

    async def _get_market_stats(self, zip_code: str) -> str:
        resp = await self._client.get(f"{self._market_url}/api/v1/market/stats/{zip_code}")
        resp.raise_for_status()
        return json.dumps(resp.json())

    async def _get_price_trends(self, zip_code: str, months: int) -> str:
        resp = await self._client.get(
            f"{self._market_url}/api/v1/market/trends/{zip_code}",
            params={"months": months},
        )
        resp.raise_for_status()
        return json.dumps(resp.json())
