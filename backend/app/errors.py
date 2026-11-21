import uuid
from typing import Any, Dict, List, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str = "",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        params: Optional[Dict[str, Any]] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.params = params or {}
        self.fields = fields or []
        super().__init__(message or code)

def format_error_response(
    code: str,
    params: Optional[Dict[str, Any]] = None,
    fields: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "params": params or {},
            "fields": fields or [],
            "request_id": request_id or str(uuid.uuid4())
        }
    }

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=exc.code,
            params=exc.params,
            fields=exc.fields,
            request_id=request_id
        )
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    sanitized_fields = []
    
    # Process errors and strictly strip 'input' and 'ctx'
    for err in exc.errors():
        loc = err.get("loc", [])
        field_name = ".".join(str(l) for l in loc if l not in ("body", "query", "path"))
        err_type = err.get("type", "value_error")
        
        # Map err_type to our error code
        code = "VALIDATION_ERROR"
        if "credential" in err_type.lower():
            code = "CREDENTIAL_INPUT_REJECTED"
        elif "invalid_text" in err_type.lower():
            code = "INVALID_TEXT"
            
        sanitized_fields.append({
            "field": field_name,
            "code": code,
            "params": {"type": err_type}
        })
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            code="VALIDATION_ERROR",
            params={},
            fields=sanitized_fields,
            request_id=request_id
        )
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHENTICATED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        code = "RATE_LIMITED"
        
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            code=code,
            params={"detail": exc.detail} if isinstance(exc.detail, str) else {},
            request_id=request_id
        )
    )
