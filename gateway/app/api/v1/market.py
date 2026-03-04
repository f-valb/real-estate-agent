"""Reverse proxy routes for the Market Data service."""
from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/api/v1/market", tags=["market"])


async def _proxy(request: Request, path: str) -> Response:
    client = request.app.state.http_client
    url = f"{request.app.state.config['MARKET_SERVICE_URL']}/api/v1/market{path}"

    body = await request.body()
    resp = await client.request(
        method=request.method,
        url=url,
        params=request.query_params,
        content=body if body else None,
        headers={"content-type": "application/json"},
    )
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.api_route("/sales", methods=["GET", "POST"])
async def sales(request: Request):
    return await _proxy(request, "/sales")


@router.get("/comps")
async def comps(request: Request):
    return await _proxy(request, "/comps")


@router.get("/stats/{zip_code}")
async def stats(zip_code: str, request: Request):
    return await _proxy(request, f"/stats/{zip_code}")


@router.post("/stats/{zip_code}/compute")
async def compute_stats(zip_code: str, request: Request):
    return await _proxy(request, f"/stats/{zip_code}/compute")


@router.get("/trends/{zip_code}")
async def trends(zip_code: str, request: Request):
    return await _proxy(request, f"/trends/{zip_code}")
