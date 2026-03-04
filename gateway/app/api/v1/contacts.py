"""Reverse proxy routes for the CRM Contact service."""
from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


async def _proxy(request: Request, path: str) -> Response:
    client = request.app.state.http_client
    url = f"{request.app.state.config['CRM_SERVICE_URL']}/api/v1/contacts{path}"

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
async def contacts_root(request: Request):
    return await _proxy(request, "")


@router.api_route("/{contact_id}", methods=["GET", "PUT", "DELETE"])
async def contact_by_id(contact_id: str, request: Request):
    return await _proxy(request, f"/{contact_id}")


@router.api_route("/{contact_id}/pipeline", methods=["PATCH"])
async def contact_pipeline(contact_id: str, request: Request):
    return await _proxy(request, f"/{contact_id}/pipeline")


@router.api_route("/{contact_id}/interactions", methods=["GET", "POST"])
async def contact_interactions(contact_id: str, request: Request):
    return await _proxy(request, f"/{contact_id}/interactions")


@router.api_route("/{contact_id}/tags", methods=["GET", "POST"])
async def contact_tags(contact_id: str, request: Request):
    return await _proxy(request, f"/{contact_id}/tags")
