"""Tool definitions and execution for the Lead Intelligence Agent."""
import json
import logging

import httpx

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_contact_details",
            "description": "Retrieve full details of a contact including type, pipeline stage, preferences, and tags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "UUID of the contact"},
                },
                "required": ["contact_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_interaction_history",
            "description": "Get the interaction history for a contact (calls, emails, showings, notes).",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "UUID of the contact"},
                    "limit": {"type": "integer", "description": "Max interactions to return", "default": 20},
                },
                "required": ["contact_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_matching_listings",
            "description": "Find property listings matching the contact's preferences (price range, bedrooms, areas).",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_price": {"type": "number", "description": "Minimum price"},
                    "max_price": {"type": "number", "description": "Maximum price"},
                    "bedrooms": {"type": "integer", "description": "Minimum bedrooms"},
                    "city": {"type": "string", "description": "City to search in"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_conditions",
            "description": "Get current market statistics for a ZIP code to understand market conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zip_code": {"type": "string", "description": "ZIP code to check"},
                },
                "required": ["zip_code"],
            },
        },
    },
]


class ToolExecutor:
    """Executes tool calls by dispatching to microservice REST APIs."""

    def __init__(self, crm_service_url: str, property_service_url: str, market_service_url: str):
        self._crm_url = crm_service_url
        self._property_url = property_service_url
        self._market_url = market_service_url
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    async def execute(self, tool_name: str, arguments: dict) -> str:
        try:
            if tool_name == "get_contact_details":
                return await self._get_contact(arguments["contact_id"])
            elif tool_name == "get_interaction_history":
                return await self._get_interactions(
                    arguments["contact_id"],
                    arguments.get("limit", 20),
                )
            elif tool_name == "get_matching_listings":
                return await self._get_listings(arguments)
            elif tool_name == "get_market_conditions":
                return await self._get_market(arguments["zip_code"])
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        except httpx.ConnectError as e:
            logger.error("Service connection error for %s: %s", tool_name, e)
            return json.dumps({"error": f"Service unavailable: {e}"})
        except Exception as e:
            logger.error("Tool execution error for %s: %s", tool_name, e)
            return json.dumps({"error": str(e)})

    async def _get_contact(self, contact_id: str) -> str:
        resp = await self._client.get(f"{self._crm_url}/api/v1/contacts/{contact_id}")
        resp.raise_for_status()
        return json.dumps(resp.json())

    async def _get_interactions(self, contact_id: str, limit: int) -> str:
        resp = await self._client.get(
            f"{self._crm_url}/api/v1/contacts/{contact_id}/interactions",
            params={"limit": limit},
        )
        resp.raise_for_status()
        return json.dumps(resp.json())

    async def _get_listings(self, args: dict) -> str:
        params = {"status": "active", "limit": 20}
        if "min_price" in args:
            params["min_price"] = args["min_price"]
        if "max_price" in args:
            params["max_price"] = args["max_price"]
        if "bedrooms" in args:
            params["bedrooms"] = args["bedrooms"]
        if "city" in args:
            params["city"] = args["city"]

        resp = await self._client.get(f"{self._property_url}/api/v1/listings", params=params)
        resp.raise_for_status()
        return json.dumps(resp.json())

    async def _get_market(self, zip_code: str) -> str:
        resp = await self._client.get(f"{self._market_url}/api/v1/market/stats/{zip_code}")
        resp.raise_for_status()
        return json.dumps(resp.json())
