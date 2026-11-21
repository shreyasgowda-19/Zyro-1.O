import os
import sys
import time
from fastapi import APIRouter, HTTPException, status, Depends
from app.config import settings
from app.errors import AppError
from app.models.entities import User
from app.security.auth import require_role

# Ensure project root is in sys.path so scripts can be imported anywhere
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.reset_demo import reset_demo

router = APIRouter(prefix="/demo", tags=["Demo"])

SCENARIOS = [
    {
        "id": "low_baseline",
        "fixture": "F1",
        "title": "Low Risk: Known Payee & Usual Amount (₹800)",
        "description": "Daytime regular grocery payment to a known merchant. Evaluates to Low band (Score 0), completes immediately.",
        "payload": {
            "amount_paise": 80000,
            "category": "Groceries",
            "payee_display_name": "Fresh Mart Groceries",
            "payee_masked_identifier": "••••1029",
            "method": "upi",
            "note": "Weekly groceries supplies",
            "simulated_at": None,
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        }
    },
    {
        "id": "medium_unusual_amount_new_payee",
        "fixture": "F2",
        "title": "Medium Risk: Unfamiliar Payee & 3.5x Amount (₹7,000)",
        "description": "First-time payment to an unknown seller with an amount 3.5x higher than usual average. Triggers R1 + R2 (Score 40–55), requires explicit confirmation.",
        "payload": {
            "amount_paise": 700000,
            "category": "Shopping",
            "payee_display_name": "Apex Electronic Hub",
            "payee_masked_identifier": "••••7777",
            "method": "upi",
            "note": "Urgent refund processing for gadget purchase",
            "simulated_at": None,
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        }
    },
    {
        "id": "high_flagged_late_night",
        "fixture": "F3",
        "title": "High Risk: Flagged Payee at 2:30 AM (₹4,000)",
        "description": "Payment to a known fraudulent payee in middle of the night with pressure note. Triggers R6 + R3 + R8 (Score 80), held for human review with reserved funds.",
        "payload": {
            "amount_paise": 400000,
            "category": "Utilities",
            "payee_display_name": "Suspicious Tele-Services",
            "payee_masked_identifier": "••••9941",
            "method": "upi",
            "note": "Urgent electricity bill clearance",
            "simulated_at": "2026-11-21T02:30:00+05:30",
            "synthetic_device_tag": "D9",
            "synthetic_city_tag": "Delhi"
        }
    },
    {
        "id": "high_burst_velocity",
        "fixture": "F4",
        "title": "High Risk: Velocity Burst Pattern",
        "description": "Rapid successive payments mimicking account takeover. Triggers R4 High Velocity (Score 70+), held for human review.",
        "payload": {
            "amount_paise": 650000,
            "category": "Shopping",
            "payee_display_name": "Fast Delivery Retail",
            "payee_masked_identifier": "••••3320",
            "method": "upi",
            "note": "Immediate payment 4 of 4",
            "simulated_at": None,
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        }
    },
    {
        "id": "high_collect_request",
        "fixture": "F5",
        "title": "High Risk: Unknown Collect Request Scam (₹2,500)",
        "description": "Incoming UPI collect approval request from unfamiliar requester with scam note. Triggers R10 + R2 + R8 (Score 70+), held for review.",
        "payload": {
            "amount_paise": 250000,
            "category": "General",
            "payee_display_name": "Income Tax Refund Cell",
            "payee_masked_identifier": "••••5544",
            "method": "collect_approval",
            "note": "Tax refund lottery prize clearance",
            "simulated_at": None,
            "synthetic_device_tag": "D5",
            "synthetic_city_tag": "Kolkata"
        }
    }
]

@router.get("/scenarios")
def get_demo_scenarios():
    if not settings.DEMO_MODE:
        raise AppError("DEMO_MODE_DISABLED", "Demo endpoints disabled in production", status_code=400)
    return {"scenarios": SCENARIOS}

@router.post("/reset")
def reset_demo_database(current_user: User = Depends(require_role("supervisor"))):
    if not settings.DEMO_MODE:
        raise AppError("DEMO_MODE_DISABLED", "Demo reset disabled in production", status_code=400)
    start_time = time.time()
    reset_demo()
    duration = time.time() - start_time
    return {
        "status": "ok",
        "message": f"Demo database reset and re-seeded successfully in {duration:.2f} seconds.",
        "duration_seconds": round(duration, 3)
    }
