import os
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings, BASE_DIR
from app.errors import AppError, app_error_handler, validation_error_handler, http_exception_handler
from app.routers import auth, health, payments, transactions, accounting, review, alerts, demo, risk, budgets, goals, guidance

limiter = Limiter(key_func=get_remote_address)

def perform_startup_checks():
    """Verify required configuration, JWT secrets, risk rules schema, and DB connectivity."""
    # 1. JWT secret check
    if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 16:
        raise RuntimeError("FATAL: JWT_SECRET must be at least 16 characters long.")

    # 2. Risk rules schema check
    rules_path = os.path.join(BASE_DIR, settings.RULES_CONFIG_PATH)
    if not os.path.exists(rules_path):
        raise RuntimeError(f"FATAL: risk_rules.json missing at {rules_path}")

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
        if "rules_version" not in rules_data or "rules" not in rules_data:
            raise RuntimeError("FATAL: risk_rules.json missing required top-level keys.")
        for r_code in [f"R{i}" for i in range(1, 11)]:
            if r_code not in rules_data["rules"]:
                raise RuntimeError(f"FATAL: risk_rules.json missing rule {r_code}")
    except Exception as e:
        raise RuntimeError(f"FATAL: Failed to validate risk_rules.json: {e}")

    # 3. Database connectivity check
    from app.database import engine
    try:
        with engine.connect() as conn:
            pass
    except Exception as e:
        raise RuntimeError(f"FATAL: Database connection failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    perform_startup_checks()
    yield

app = FastAPI(
    title="PayGuard 360 API",
    description="Fraud-first financial safety platform for India — Prototype API",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Request ID & Logging Middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response

# Security Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(payments.router)
app.include_router(transactions.router)
app.include_router(accounting.router)
app.include_router(review.router)
app.include_router(alerts.router)
app.include_router(demo.router)
app.include_router(risk.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(guidance.router)
