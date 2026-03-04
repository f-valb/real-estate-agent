"""Reverse proxy routes for the Property Listing service."""
import logging

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/listings", tags=["listings"])


async def _proxy(request: Request, path: str) -> Response:
    client = request.app.state.http_client
    url = f"{request.app.state.config['PROPERTY_SERVICE_URL']}/api/v1/listings{path}"

    body = await request.body()
    resp = await client.request(
        method=request.method,
        url=url,
        params=request.query_params,
        content=body if body else None,
        headers={"content-type": "application/json"},
    )
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.api_route("", methods=["GET", "POST"])
async def listings_root(request: Request):
    return await _proxy(request, "")


@router.api_route("/{listing_id}", methods=["GET", "PUT", "DELETE"])
async def listing_by_id(listing_id: str, request: Request):
    return await _proxy(request, f"/{listing_id}")


@router.api_route("/{listing_id}/status", methods=["PATCH"])
async def listing_status(listing_id: str, request: Request):
    return await _proxy(request, f"/{listing_id}/status")
