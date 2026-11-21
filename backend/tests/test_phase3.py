import os
import sys
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database import engine, SessionLocal
from app.models.entities import Transaction, Budget, SavingsGoal, Alert, User
from scripts.reset_demo import reset_demo

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_before_tests():
    engine.dispose()
    reset_demo()
    yield
    engine.dispose()

def get_auth_token(username: str) -> str:
    res = client.post("/auth/login", json={"username": username, "password": "password123"})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    return res.json()["access_token"]


# ============================================================================
# 1. BUDGET CRUD & RBAC TESTS (§13, §17)
# ============================================================================

def test_budget_crud_and_rbac():
    rahul_token = get_auth_token("rahul_personal")
    priya_token = get_auth_token("priya_personal")
    reviewer_token = get_auth_token("ananya_reviewer")

    # 1. Reviewer forbidden from accessing customer budgets
    rev_res = client.get("/budgets", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert rev_res.status_code == 403

    # 2. List Rahul's seeded budgets
    list_res = client.get("/budgets", headers={"Authorization": f"Bearer {rahul_token}"})
    assert list_res.status_code == 200
    budgets = list_res.json()
    assert len(budgets) >= 4  # Seeded with overall + 3 categories

    # 3. Create a new category budget for Entertainment (₹5,000 = 500,000 paise)
    current_period = datetime.now(timezone.utc).strftime("%Y-%m")
    create_res = client.post(
        "/budgets",
        json={
            "category": "Entertainment",
            "amount_paise": 500000,
            "period": current_period
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )
    assert create_res.status_code == 201
    created_budget = create_res.json()
    budget_id = created_budget["id"]
    assert created_budget["category"] == "Entertainment"
    assert created_budget["amount_paise"] == 500000

    # 4. Modify budget amount to ₹6,000
    mod_res = client.put(
        f"/budgets/{budget_id}",
        json={"amount_paise": 600000},
        headers={"Authorization": f"Bearer {rahul_token}"}
    )
    assert mod_res.status_code == 200
    assert mod_res.json()["amount_paise"] == 600000

    # 5. IDOR Protection: Priya cannot modify Rahul's budget
    priya_mod = client.put(
        f"/budgets/{budget_id}",
        json={"amount_paise": 100000},
        headers={"Authorization": f"Bearer {priya_token}"}
    )
    assert priya_mod.status_code == 404

    # 6. Delete budget
    del_res = client.delete(f"/budgets/{budget_id}", headers={"Authorization": f"Bearer {rahul_token}"})
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"


# ============================================================================
# 2. BUDGET SUMMARY ACCURACY (COMPLETED EXPENSES ONLY) (§8, §13)
# ============================================================================

def test_budget_summary_counts_only_completed_expenses():
    rahul_token = get_auth_token("rahul_personal")
    current_period = datetime.now(timezone.utc).strftime("%Y-%m")

    # Get baseline summary
    sum_0 = client.get(f"/budgets/summary?period={current_period}", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    initial_spent = sum_0["overall"]["spent_paise"]

    # 1. Add a completed manual expense (₹1,000 = 100,000 paise in Groceries)
    tx_res = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount_paise": 100000,
            "category": "Groceries",
            "note": "Supermarket purchase"
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )
    assert tx_res.status_code == 200

    # Summary must immediately reflect completed expense
    sum_1 = client.get(f"/budgets/summary?period={current_period}", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert sum_1["overall"]["spent_paise"] == initial_spent + 100000

    # 2. Add a High-risk payment that gets HELD (₹4,000 = 400,000 paise in Utilities)
    hold_res = client.post(
        "/payments",
        json={
            "amount_paise": 400000,
            "category": "Utilities",
            "payee_display_name": "Suspicious Tele-Services",
            "payee_masked_identifier": "••••9941",
            "method": "upi",
            "note": "Urgent electricity bill clearance",
            "simulated_at": "2026-11-21T02:30:00+05:30",
            "synthetic_device_tag": "D9",
            "synthetic_city_tag": "Delhi"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "test-budget-held-001"
        }
    )
    assert hold_res.status_code == 200
    assert hold_res.json()["status"] == "held"

    # Held transaction MUST NOT count towards spent budget! (§8, §13, D7)
    sum_2 = client.get(f"/budgets/summary?period={current_period}", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert sum_2["overall"]["spent_paise"] == initial_spent + 100000


# ============================================================================
# 3. 80% AND 100% BUDGET ALERT ENGINE (§13)
# ============================================================================

def test_budget_alerts_80_and_100_percent_firing_and_deduplication():
    rahul_token = get_auth_token("rahul_personal")
    current_period = datetime.now(timezone.utc).strftime("%Y-%m")

    # Set a budget of ₹10,000 (1,000,000 paise) for "Health"
    b_res = client.post(
        "/budgets",
        json={
            "category": "Health",
            "amount_paise": 1000000,
            "period": current_period
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )
    assert b_res.status_code == 201

    # 1. Spend ₹7,500 (750,000 paise = 75%) -> Under 80%, no alert
    client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount_paise": 750000,
            "category": "Health",
            "note": "Pharmacy bill"
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )

    alerts_res_1 = client.get("/alerts", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    health_alerts_1 = [a for a in alerts_res_1["items"] if a.get("params", {}).get("category") == "Health"]
    assert len(health_alerts_1) == 0

    # 2. Spend ₹1,000 (100,000 paise) -> Total ₹8,500 = 85% -> 80% Warning Alert Fires!
    client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount_paise": 100000,
            "category": "Health",
            "note": "Consultation fee"
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )

    alerts_res_2 = client.get("/alerts", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    health_alerts_2 = [a for a in alerts_res_2["items"] if a.get("params", {}).get("category") == "Health"]
    assert len(health_alerts_2) == 1
    assert health_alerts_2[0]["title_code"] == "alert.budget.approaching_limit"
    assert health_alerts_2[0]["params"]["percentage"] == 85.0

    # 3. Spend another ₹200 (20,000 paise) -> Total ₹8,700 = 87% -> Deduplication prevents duplicate 80% alert!
    client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount_paise": 20000,
            "category": "Health",
            "note": "Medicine supplement"
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )

    alerts_res_3 = client.get("/alerts", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    health_alerts_3 = [a for a in alerts_res_3["items"] if a.get("params", {}).get("category") == "Health"]
    assert len(health_alerts_3) == 1  # Still exactly 1 due to deduplication

    # 4. Spend ₹1,500 (150,000 paise) -> Total ₹10,200 = 102% -> 100% Exceeded Alert Fires!
    client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount_paise": 150000,
            "category": "Health",
            "note": "Lab diagnostics"
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )

    alerts_res_4 = client.get("/alerts", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    health_alerts_4 = [a for a in alerts_res_4["items"] if a.get("params", {}).get("category") == "Health"]
    assert len(health_alerts_4) == 2
    exceeded_alert = next((a for a in health_alerts_4 if a["title_code"] == "alert.budget.limit_exceeded"), None)
    assert exceeded_alert is not None
    assert exceeded_alert["params"]["percentage"] >= 100.0


# ============================================================================
# 4. SAVINGS GOALS CRUD & CONTRIBUTIONS (§13, §17)
# ============================================================================

def test_savings_goals_crud_and_contributions():
    rahul_token = get_auth_token("rahul_personal")
    priya_token = get_auth_token("priya_personal")

    # 1. List Rahul's seeded goals
    goals_res = client.get("/goals", headers={"Authorization": f"Bearer {rahul_token}"})
    assert goals_res.status_code == 200
    goals = goals_res.json()
    assert len(goals) >= 2

    # 2. Create a new goal: "Solar Inverter" (Target: ₹30,000 = 3,000,000 paise)
    create_res = client.post(
        "/goals",
        json={
            "title": "Solar Inverter",
            "target_paise": 3000000,
            "target_date": "2026-12-31"
        },
        headers={"Authorization": f"Bearer {rahul_token}"}
    )
    assert create_res.status_code == 201
    goal = create_res.json()
    goal_id = goal["id"]
    assert goal["title"] == "Solar Inverter"
    assert goal["target_paise"] == 3000000
    assert goal["current_paise"] == 0
    assert goal["progress_percentage"] == 0.0

    # 3. Contribute ₹6,000 (600,000 paise) to goal (20% progress)
    contrib_res = client.post(
        f"/goals/{goal_id}/contributions",
        json={"amount_paise": 600000},
        headers={"Authorization": f"Bearer {rahul_token}"}
    )
    assert contrib_res.status_code == 200
    updated_goal = contrib_res.json()
    assert updated_goal["current_paise"] == 600000
    assert updated_goal["progress_percentage"] == 20.0

    # 4. Over-contribution rejection: Attempt to contribute more than available ledger balance
    bal_res = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    avail = bal_res["available_balance_paise"]

    over_res = client.post(
        f"/goals/{goal_id}/contributions",
        json={"amount_paise": avail + 1000000},
        headers={"Authorization": f"Bearer {rahul_token}"}
    )
    assert over_res.status_code == 409
    assert over_res.json()["error"]["code"] == "INSUFFICIENT_FUNDS"

    # 5. IDOR Protection: Priya cannot view or contribute to Rahul's goal
    priya_contrib = client.post(
        f"/goals/{goal_id}/contributions",
        json={"amount_paise": 10000},
        headers={"Authorization": f"Bearer {priya_token}"}
    )
    assert priya_contrib.status_code == 404

    # 6. Delete goal
    del_res = client.delete(f"/goals/{goal_id}", headers={"Authorization": f"Bearer {rahul_token}"})
    assert del_res.status_code == 200


# ============================================================================
# 5. CASH FLOW & CATEGORY ANALYTICS ENDPOINTS (§13)
# ============================================================================

def test_accounting_cashflow_and_category_analytics():
    rahul_token = get_auth_token("rahul_personal")
    current_period = datetime.now(timezone.utc).strftime("%Y-%m")

    # 1. Cash flow analytics
    cf_res = client.get(f"/accounting/cashflow?period={current_period}", headers={"Authorization": f"Bearer {rahul_token}"})
    assert cf_res.status_code == 200
    cf_data = cf_res.json()
    assert "total_income_paise" in cf_data
    assert "total_expenses_paise" in cf_data
    assert "net_cashflow_paise" in cf_data
    assert "daily" in cf_data
    assert cf_data["net_cashflow_paise"] == cf_data["total_income_paise"] - cf_data["total_expenses_paise"]

    # 2. Category analytics
    cat_res = client.get(f"/accounting/categories?period={current_period}", headers={"Authorization": f"Bearer {rahul_token}"})
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    assert "total_spent_paise" in cat_data
    assert "categories" in cat_data
    assert len(cat_data["categories"]) > 0
    # Percentages must sum close to 100% if spending exists
    if cat_data["total_spent_paise"] > 0:
        total_pct = sum(c["percentage"] for c in cat_data["categories"])
        assert 99.0 <= total_pct <= 101.0
