import json
import os
from fastapi import APIRouter
from app.config import settings, BASE_DIR
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health():
    # Load rules version from risk_rules.json
    rules_path = os.path.join(BASE_DIR, settings.RULES_CONFIG_PATH)
    rules_version = "unknown"
    if os.path.exists(rules_path):
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                rules_version = data.get("rules_version", "unknown")
        except Exception:
            pass

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        schema_head="48b4197d4d1e",
        rules_version=rules_version,
        demo_mode=settings.DEMO_MODE
    )
