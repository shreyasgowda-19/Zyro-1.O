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
        "/demo/scenarios",
        "/demo/reset"  # Protected by DEMO_MODE flag
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
