from http import HTTPStatus


class AppError(Exception):
    """Base application error with HTTP status code and error code."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: list[dict] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found", details: list[dict] | None = None) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
            details=details,
        )


class ConflictError(AppError):
    """Resource conflict (409)."""

    def __init__(self, message: str = "Resource already exists", details: list[dict] | None = None) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=HTTPStatus.CONFLICT,
            details=details,
        )


class UnauthorizedError(AppError):
    """Authentication required (401)."""

    def __init__(self, message: str = "Authentication required", details: list[dict] | None = None) -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=HTTPStatus.UNAUTHORIZED,
            details=details,
        )
