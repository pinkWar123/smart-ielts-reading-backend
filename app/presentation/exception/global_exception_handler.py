import logging
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode

logger = logging.getLogger(__name__)

HTTP_STATUS_MAPPINGS: Dict[ErrorCode, int] = {
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.INVALID_DATA: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.CONFLICT: 409,
    ErrorCode.BAD_REQUEST: 400,
    ErrorCode.INTERNAL_ERROR: 500,
}


def get_error_details(
    exc: Exception, include_debug: bool = False
) -> Optional[Dict[str, Any]]:
    if not include_debug:
        return None

    return {
        "exception_type": type(exc).__name__,
        "traceback": str(exc.__traceback__) if exc.__traceback__ else None,
        "args": exc.args if exc.args else None,
    }


def setup_exception_handlers(app: FastAPI):
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"

    @app.exception_handler(Error)
    async def domain_error_handler(request: Request, exc: Error):
        logger.warning(
            logger.warning(f"Domain error: {exc.code.value} - {exc.message}")
        )

        details = None
        if hasattr(exc, "details") and exc.details:
            details = exc.details
        elif debug_mode:
            details = {"exception_type": type(exc).__name__}
        return JSONResponse(
            status_code=HTTP_STATUS_MAPPINGS[exc.code],
            content={
                "error_code": HTTP_STATUS_MAPPINGS[exc.code],
                "message": exc.message,
                "details": details,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": get_error_details(exc, debug_mode),
            },
        )
