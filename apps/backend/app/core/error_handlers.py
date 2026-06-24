import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError, NotFoundError

logger = structlog.get_logger(__name__)


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(loc) for loc in e["loc"]),
            "reason": e["msg"],
        }
        for e in exc.errors()
    ]
    logger.warning(
        "validation_error",
        path=request.url.path,
        method=request.method,
        details=details,
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
            }
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning(
        "integrity_error",
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=409,
        content={
            "error": {
                "code": "CONFLICT",
                "message": "Resource already exists",
                "details": [],
            }
        },
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    logger.warning(
        "not_found",
        path=request.url.path,
        method=request.method,
        message=exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.error(
        "app_error",
        path=request.url.path,
        method=request.method,
        code=exc.code,
        message=exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error",
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": [],
            }
        },
    )
