"""Tool definitions and executor for the Home Finder agent."""
import json
import logging

import httpx

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_listings",
            "description": (
                "Search active property listings by location, price range, and bedroom count. "
                "Returns a list of matching listings with their details. "
                "All parameters are optional — omit any you don't have information about."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to search in (e.g. 'Austin', 'Dallas'). Case-insensitive partial match.",
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "ZIP code to search in (e.g. '78701'). Takes priority over city.",
                    },
                    "min_price": {
                        "type": "integer",
                        "description": "Minimum list price in dollars (e.g. 300000 for $300k).",
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "Maximum list price in dollars (e.g. 500000 for $500k).",
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Minimum number of bedrooms required (e.g. 3 means at least 3 bedrooms).",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return. Defaults to 20.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_listing_details",
            "description": "Get full details for a specific property listing by ID. Use this to enrich a listing you already found.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "The UUID of the property listing.",
                    },
                },
                "required": ["property_id"],
            },
        },
    },
]


class ToolExecutor:
    def __init__(self, property_service_url: str):
        self.property_url = property_service_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def execute(self, tool_name: str, arguments: dict) -> str:
        try:
            if tool_name == "search_listings":
                return await self._search_listings(**arguments)
            elif tool_name == "get_listing_details":
                return await self._get_listing_details(**arguments)
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        except httpx.ConnectError as e:
            logger.error("Connection error calling tool %s: %s", tool_name, e)
            return json.dumps({"error": "Service unavailable", "tool": tool_name})
        except Exception as e:
            logger.error("Tool %s failed: %s", tool_name, e)
            return json.dumps({"error": str(e), "tool": tool_name})

    async def _search_listings(
        self,
        city: str | None = None,
        zip_code: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        bedrooms: int | None = None,
        limit: int = 20,
    ) -> str:
        params: dict = {"status": "active", "limit": min(limit, 100)}
        if city:
            params["city"] = city
        if zip_code:
            params["zip_code"] = zip_code
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if bedrooms is not None:
            params["bedrooms"] = bedrooms

        logger.info("search_listings params: %s", params)
        resp = await self._client.get(f"{self.property_url}/api/v1/listings", params=params)
        resp.raise_for_status()
        data = resp.json()
        logger.info("search_listings returned %d / %d total", len(data.get("items", [])), data.get("total", 0))
        return json.dumps(data)

    async def _get_listing_details(self, property_id: str) -> str:
        resp = await self._client.get(f"{self.property_url}/api/v1/listings/{property_id}")
        resp.raise_for_status()
        return json.dumps(resp.json())

    async def close(self):
        await self._client.aclose()
