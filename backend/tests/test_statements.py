import os
import sys
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import Base, get_db
from app.clock import utcnow
from app.main import app
from app.models.entities import User
from app.security.auth import hash_password


@pytest.fixture
def statement_client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    test_sessions = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = test_sessions()
    db.add_all([
        User(username="statement_customer", password_hash=hash_password("customer-pass-123"), role="customer", profile_type="personal", is_active=True),
        User(username="statement_other", password_hash=hash_password("other-pass-123"), role="customer", profile_type="personal", is_active=True),
        User(username="statement_manager", password_hash=hash_password("manager-pass-123"), role="supervisor", profile_type=None, is_active=True),
    ])
    db.commit()
    db.close()

    def override_get_db():
        session = test_sessions()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def token(client, username, password):
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_csv_import_is_idempotent_and_manager_approves_statement(statement_client):
    client = statement_client
    customer_headers = token(client, "statement_customer", "customer-pass-123")
    other_headers = token(client, "statement_other", "other-pass-123")
    manager_headers = token(client, "statement_manager", "manager-pass-123")
    today = utcnow().date()
    import_payload = {
        "file_hash": "a" * 64,
        "rows": [
            {
                "type": "expense",
                "amount_paise": 12345,
                "category": "Groceries",
                "note": "Market purchase",
                "created_at": f"{today.isoformat()}T10:00:00+05:30",
                "row_number": 2,
            },
            {
                "type": "income",
                "amount_paise": 500000,
                "category": "Income",
                "note": "Monthly salary",
                "created_at": f"{today.isoformat()}T11:00:00+05:30",
                "row_number": 3,
            },
        ],
    }
    imported = client.post("/statements/import", json=import_payload, headers=customer_headers)
    assert imported.status_code == 200
    assert imported.json()["imported_count"] == 2
    replay = client.post("/statements/import", json=import_payload, headers=customer_headers)
    assert replay.status_code == 200
    assert replay.json()["imported_count"] == 0
    assert replay.json()["duplicates_skipped"] == 2

    request_payload = {
        "start_date": (today - timedelta(days=1)).isoformat(),
        "end_date": today.isoformat(),
    }
    request = client.post("/statements/requests", json=request_payload, headers=customer_headers)
    assert request.status_code == 201
    request_id = request.json()["id"]
    assert request.json()["transaction_count"] == 2

    pending_download = client.get(f"/statements/requests/{request_id}/download", headers=customer_headers)
    assert pending_download.status_code == 403
    queue = client.get("/statements/requests/queue", headers=manager_headers)
    assert queue.status_code == 200
    assert queue.json()[0]["requester_username"] == "statement_customer"
    assert client.get("/statements/requests/queue", headers=customer_headers).status_code == 403
    preview = client.get(f"/statements/requests/{request_id}/preview", headers=manager_headers)
    assert preview.status_code == 200
    assert preview.json()["total_count"] == 2
    assert preview.json()["rows"][0]["description"] == "Market purchase"
    assert client.get(f"/statements/requests/{request_id}/preview", headers=customer_headers).status_code == 403

    decision = client.post(
        f"/statements/requests/{request_id}/decision",
        json={"decision": "approved", "note": "Customer request reviewed and approved."},
        headers=manager_headers,
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"
    alerts = client.get("/alerts", headers=customer_headers)
    assert alerts.status_code == 200
    assert any(item["title_code"] == "alert.statement.approved" for item in alerts.json()["items"])
    assert client.get(f"/statements/requests/{request_id}/download", headers=other_headers).status_code == 404
    download = client.get(f"/statements/requests/{request_id}/download", headers=customer_headers)
    assert download.status_code == 200
    assert "Market purchase" in download.text
    assert "Customer entered" in download.text
