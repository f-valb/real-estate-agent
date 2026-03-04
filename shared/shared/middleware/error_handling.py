import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


class ServiceUnavailableError(Exception):
    def __init__(self, service: str):
        self.service = service
        super().__init__(f"Service unavailable: {service}")


async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": f"Downstream service unavailable: {exc.service}"},
    )
