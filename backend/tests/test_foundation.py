import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database import Base, get_db, create_append_only_triggers
from app.models.entities import User, AuditLog, ReviewCase, ReviewCaseAction
from app.security.auth import hash_password, create_access_token

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["rules_version"] == "1.0.0"
    assert data["demo_mode"] is True

def test_login_successful():
    response = client.post("/auth/login", json={
        "username": "rahul_personal",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "rahul_personal"
    assert data["user"]["role"] == "customer"
    assert data["user"]["profile_type"] == "personal"

def test_login_invalid_password():
    response = client.post("/auth/login", json={
        "username": "rahul_personal",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"

def test_users_me_authenticated():
    # Login first
    login_res = client.post("/auth/login", json={
        "username": "ananya_reviewer",
        "password": "password123"
    })
    token = login_res.json()["access_token"]

    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "ananya_reviewer"
    assert data["role"] == "reviewer"

def test_users_me_unauthenticated():
    response = client.get("/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"

def test_users_me_forged_token():
    forged_token = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJzdWIiOiAiMSJ9.fake_signature"
    response = client.get("/users/me", headers={"Authorization": f"Bearer {forged_token}"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"

def test_append_only_triggers():
    """Verify that SQLite triggers prevent UPDATE and DELETE on audit_log and review_case_actions."""
    import sqlite3
    from app.config import settings
    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find an audit log record
    cursor.execute("SELECT id FROM audit_log LIMIT 1")
    row = cursor.fetchone()
    assert row is not None
    audit_id = row[0]

    # Attempt UPDATE on audit_log
    with pytest.raises(sqlite3.DatabaseError) as exc_info:
        cursor.execute("UPDATE audit_log SET action='tampered' WHERE id=?", (audit_id,))
    assert "append-only" in str(exc_info.value).lower()

    # Attempt DELETE on audit_log
    with pytest.raises(sqlite3.DatabaseError) as exc_info:
        cursor.execute("DELETE FROM audit_log WHERE id=?", (audit_id,))
    assert "append-only" in str(exc_info.value).lower()

    conn.close()
