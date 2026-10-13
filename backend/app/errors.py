"""One error shape for every failure: {"error": {"code", "message", "details", "request_id"}}."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class ConflictError(AppError):
    status_code = 409

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, resource: str):
        super().__init__(f"{resource.capitalize()} not found")
        self.code = f"{resource.upper()}_NOT_FOUND"


def _error(request: Request, status_code: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"code": code, "message": message, "request_id": getattr(request.state, "request_id", None)}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return _error(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = [
            # loc looks like ("body", "subject") or ("query", "page"); keep the field name
            {"field": ".".join(str(p) for p in err["loc"][1:]) or str(err["loc"][0]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return _error(request, 422, "VALIDATION_ERROR", "Request validation failed", details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        return _error(request, exc.status_code, f"HTTP_{exc.status_code}", str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # Never leak internals to the client; the request_id lets us find it in logs.
        return _error(request, 500, "INTERNAL_ERROR", "Unexpected server error")
