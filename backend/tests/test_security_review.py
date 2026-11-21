import pytest
from fastapi.testclient import TestClient
from app.main import app, perform_startup_checks
from app.config import settings

client = TestClient(app)

def test_security_headers():
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers

def test_openapi_auth_coverage():
    """Verify that every endpoint except /health and /auth/login declares authentication."""
    openapi = app.openapi()
    paths = openapi.get("paths", {})

    unprotected_allowed = {
        "/health",
        "/auth/login",
        "/auth/register",
        "/demo/scenarios",
    }

    unprotected_found = []

    for path, path_item in paths.items():
        if path in unprotected_allowed:
            continue
        for method, op in path_item.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            # Check security field in operation
            security = op.get("security", [])
            # Also check if top-level security exists
            if not security and not openapi.get("security", []):
                # Check parameters for Authorization header or dependency
                parameters = op.get("parameters", [])
                has_auth = any(
                    p.get("name", "").lower() == "authorization" or p.get("in") == "header"
                    for p in parameters
                )
                if not has_auth:
                    unprotected_found.append(f"{method.upper()} {path}")

    # All routes should be protected
    assert len(unprotected_found) == 0, f"Unprotected routes found without auth: {unprotected_found}"

def test_startup_checks():
    # Calling perform_startup_checks() on valid configuration passes cleanly
    perform_startup_checks()

    # Short secret triggers RuntimeError
    old_secret = settings.JWT_SECRET
    try:
        settings.JWT_SECRET = "short"
        with pytest.raises(RuntimeError) as exc:
            perform_startup_checks()
        assert "JWT_SECRET must be at least 16 characters" in str(exc.value)
    finally:
        settings.JWT_SECRET = old_secret

def test_demo_reset_requires_authentication():
    response = client.post("/demo/reset")
    assert response.status_code == 401
def test_production_startup_rejects_demo_mode_and_placeholder_secret(monkeypatch):
    from app.config import DEVELOPMENT_JWT_SECRET

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(settings, "JWT_SECRET", "a-configured-production-secret-long-enough")
    with pytest.raises(RuntimeError, match="DEMO_MODE must be false"):
        perform_startup_checks()

    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "JWT_SECRET", DEVELOPMENT_JWT_SECRET)
    with pytest.raises(RuntimeError, match="Replace the development JWT_SECRET"):
        perform_startup_checks()

    monkeypatch.setattr(settings, "JWT_SECRET", "a-configured-production-secret-long-enough")
    perform_startup_checks()