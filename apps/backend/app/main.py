import time
import uuid

import structlog
import structlog.contextvars
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.companies import router as companies_router
from app.core.config import settings
from app.core.error_handlers import (
    app_error_handler,
    integrity_error_handler,
    not_found_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.exceptions import AppError, NotFoundError
from app.core.rate_limit import RateLimitMiddleware

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Startup Engine API",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEMO_MODE else None,
    redoc_url="/redoc" if settings.DEMO_MODE else None,
)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id
        start = time.monotonic()

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        logger.info(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
        )
        structlog.contextvars.clear_contextvars()
        return response


app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(companies_router, prefix="/api/v1")

app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(NotFoundError, not_found_error_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.on_event("startup")
async def startup_event():
    logger.info("Startup Engine API starting", version=settings.APP_VERSION)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Startup Engine API shutting down")
