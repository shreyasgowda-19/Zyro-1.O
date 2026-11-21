import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.entities import (
    Transaction, RiskAssessment, RiskReason, ReviewCase, Alert,
    Payee, User, IdempotencyRecord, AuditLog
)
from app.services.accounting_service import verify_available_funds, get_ledger_balances
from app.services.risk_engine import evaluate_risk
from app.services.credential_guard import validate_sensitive_input
from app.clock import validate_and_resolve_time
from app.config import settings, BASE_DIR
from app.errors import AppError

LEGAL_TRANSITIONS = {
    (None, "pending"),
    ("pending", "completed"),
    ("pending", "awaiting_confirmation"),
    ("pending", "held"),
    ("awaiting_confirmation", "completed"),
    ("awaiting_confirmation", "cancelled"),
    ("held", "completed"),
    ("held", "released"),
    ("held", "escalated"),
    ("escalated", "completed"),
    ("escalated", "released"),
}

TERMINAL_STATES = {"completed", "cancelled", "released"}

def validate_transition(from_status: Optional[str], to_status: str):
    """Enforce central state transition rules (§9)."""
    if (from_status, to_status) not in LEGAL_TRANSITIONS:
        raise AppError(
            code="ILLEGAL_TRANSITION",
            message=f"Cannot transition transaction status from '{from_status}' to '{to_status}'.",
            status_code=400,
            params={"from_status": from_status, "to_status": to_status}
        )

def load_rules_config() -> Dict[str, Any]:
    import os
    rules_path = os.path.join(BASE_DIR, settings.RULES_CONFIG_PATH)
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_scoring_context(db: Session, user: User, payee: Optional[Payee], is_new_payee: bool) -> Dict[str, Any]:
    """Load consistent snapshot of customer history for pure risk engine (§10)."""
    balances = get_ledger_balances(db, user.id)

    # 1. Completed expenses (most recent first)
    completed_txs = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.type == "expense",
        Transaction.status == "completed"
    ).order_by(Transaction.created_at.desc()).all()

    completed_expenses = [
        {"amount_paise": t.amount_paise, "created_at": t.created_at}
        for t in completed_txs
    ]

    # 2. Counted payments (velocity, repeat, tag history)
    # status in ('pending', 'awaiting_confirmation', 'held', 'escalated', 'completed')
    counted_statuses = ["pending", "awaiting_confirmation", "held", "escalated", "completed"]
    counted_txs = db.query(Transaction).filter(
        Transaction.user_id == user.id,
        Transaction.source == "payment",
        Transaction.status.in_(counted_statuses)
    ).order_by(Transaction.created_at.desc()).all()

    counted_payments = [
        {
            "payee_id": t.payee_id,
            "amount_paise": t.amount_paise,
            "created_at": t.created_at,
            "device_tag": t.synthetic_device_tag,
            "city_tag": t.synthetic_city_tag
        }
        for t in counted_txs
    ]

    # 3. Tag history
    tag_devices = {t.synthetic_device_tag for t in counted_txs if t.synthetic_device_tag}
    tag_cities = {t.synthetic_city_tag for t in counted_txs if t.synthetic_city_tag}

    return {
        "completed_expenses": completed_expenses,
        "counted_payments": counted_payments,
        "tag_history_devices": list(tag_devices),
        "tag_history_cities": list(tag_cities),
        "available_balance_paise": balances["available_balance_paise"],
        "payee_trust_status": payee.trust_status if payee else "new",
        "profile_type": user.profile_type or "personal",
        "is_new_payee": is_new_payee
    }

def handle_idempotency_check(db: Session, user_id: int, key: str, payload_bytes: bytes) -> Optional[Dict[str, Any]]:
    req_hash = hashlib.sha256(payload_bytes).hexdigest()
    rec = db.query(IdempotencyRecord).filter(
        IdempotencyRecord.user_id == user_id,
        IdempotencyRecord.key == key
    ).first()

    if rec:
        if rec.request_hash == req_hash:
            return json.loads(rec.response_json)
        else:
            raise AppError(
                code="IDEMPOTENCY_CONFLICT",
                message="Idempotency key reused with different request payload.",
                status_code=409,
                params={"key": key}
            )
    return None

def save_idempotency_record(db: Session, user_id: int, key: str, payload_bytes: bytes, response_data: Dict[str, Any]):
    req_hash = hashlib.sha256(payload_bytes).hexdigest()
    rec = IdempotencyRecord(
        user_id=user_id,
        key=key,
        request_hash=req_hash,
        response_json=json.dumps(response_data)
    )
    db.add(rec)

def create_payment(
    db: Session,
    user: User,
    payment_data: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    raw_payload_bytes: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Submits and scores a simulated payment (§8, §9, §10, §11):
    1. Idempotency check
    2. Input validation & credential guard
    3. Funds verification (INSUFFICIENT_FUNDS before scoring)
    4. Payee lookup/creation
    5. Pure risk scoring
    6. Atomic status transition & balance reservation
    """
    # 1. Idempotency Check
    if idempotency_key and raw_payload_bytes:
        cached = handle_idempotency_check(db, user.id, idempotency_key, raw_payload_bytes)
        if cached:
            return cached

    # 2. Validate amount & parameters
    amount_paise = int(payment_data.get("amount_paise", 0))
    if amount_paise < 100 or amount_paise > 20000000:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Payment amount must be between 100 paise (₹1) and 20,000,000 paise (₹2,00,000).",
            status_code=422,
            params={"amount_paise": amount_paise}
        )

    # 3. Credential Guard on note and free-text fields
    raw_note = payment_data.get("note", "")
    safe_note = validate_sensitive_input(raw_note, "note") if raw_note else None

    raw_payee_name = payment_data.get("payee_display_name", "")
    safe_payee_name = validate_sensitive_input(raw_payee_name, "payee_display_name") if raw_payee_name else "Payee"

    method = payment_data.get("method", "upi")
    if method not in ("upi", "card", "netbanking", "wallet", "collect_approval"):
        raise AppError("VALIDATION_ERROR", f"Invalid payment method: {method}", status_code=422)

    # 4. Resolve time (handles simulated_at when DEMO_MODE=true)
    created_at = validate_and_resolve_time(payment_data.get("simulated_at"))

    # 5. Check available funds BEFORE scoring (§8)
    verify_available_funds(db, user.id, amount_paise)

    # 6. Resolve Payee
    payee_id = payment_data.get("payee_id")
    masked_identifier = payment_data.get("payee_masked_identifier") or "••••0000"
    payee = None
    is_new_payee = True

    if payee_id:
        payee = db.query(Payee).filter(Payee.id == payee_id, Payee.owner_user_id == user.id).first()

    if not payee and masked_identifier and masked_identifier != "••••0000":
        payee = db.query(Payee).filter(
            Payee.owner_user_id == user.id,
            Payee.masked_identifier == masked_identifier
        ).first()

    if payee:
        # Check if user has prior counted payments to this payee
        prior_count = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.payee_id == payee.id,
            Transaction.status.in_(["pending", "awaiting_confirmation", "held", "escalated", "completed"])
        ).count()
        is_new_payee = (prior_count == 0)
        masked_identifier = payee.masked_identifier
        safe_payee_name = payee.display_name
    else:
        # Create new payee
        payee = Payee(
            owner_user_id=user.id,
            display_name=safe_payee_name,
            masked_identifier=masked_identifier,
            trust_status="new",
            created_at=created_at
        )
        db.add(payee)
        db.flush()
        is_new_payee = True

    # 7. Build Scoring Context & Run Risk Engine
    scoring_context = build_scoring_context(db, user, payee, is_new_payee)
    rules_cfg = load_rules_config()

    payment_for_scoring = {
        "amount_paise": amount_paise,
        "payee_id": payee.id,
        "payee_masked": payee.masked_identifier,
        "method": method,
        "note": safe_note,
        "synthetic_device_tag": payment_data.get("synthetic_device_tag"),
        "synthetic_city_tag": payment_data.get("synthetic_city_tag")
    }

    risk_result = evaluate_risk(scoring_context, payment_for_scoring, rules_cfg, created_at)

    # 8. Determine Target State from Risk Band (§9)
    # Low -> completed
    # Medium -> awaiting_confirmation
    # High -> held (reserve funds)
    validate_transition(None, "pending")
    if risk_result.band == "low":
        target_status = "completed"
    elif risk_result.band == "medium":
        target_status = "awaiting_confirmation"
    else:
        target_status = "held"

    validate_transition("pending", target_status)

    # 9. Create Transaction
    category = payment_data.get("category", "General")
    tx = Transaction(
        user_id=user.id,
        type="expense",
        source="payment",
        amount_paise=amount_paise,
        category=category,
        payee_id=payee.id,
        method=method,
        status=target_status,
        note=safe_note,
        synthetic_device_tag=payment_data.get("synthetic_device_tag"),
        synthetic_city_tag=payment_data.get("synthetic_city_tag"),
        created_at=created_at
    )
    db.add(tx)
    db.flush()

    # 10. Persist Risk Assessment & Reasons
    assessment = RiskAssessment(
        transaction_id=tx.id,
        score=risk_result.score,
        band=risk_result.band,
        rules_version=risk_result.rules_version,
        features_json=json.dumps(risk_result.features),
        created_at=created_at
    )
    db.add(assessment)
    db.flush()

    for r in risk_result.reasons:
        reason_row = RiskReason(
            assessment_id=assessment.id,
            rule_code=r.rule_code,
            points=r.points,
            params_json=json.dumps(r.params)
        )
        db.add(reason_row)

    # 11. Handle Lifecycle Side Effects
    if target_status == "completed":
        # First completed payment moves payee new -> known (§7)
        if payee.trust_status == "new":
            payee.trust_status = "known"

    elif target_status == "held":
        # Create hold_review Case (§9, §12)
        review_case = ReviewCase(
            transaction_id=tx.id,
            case_type="hold_review",
            status="open",
            version=1,
            created_at=created_at,
            updated_at=created_at
        )
        db.add(review_case)
        db.flush()

        # Customer alert for held payment (§9)
        alert = Alert(
            user_id=user.id,
            type="fraud",
            title_code="alert.fraud.held_notice",
            params_json=json.dumps({
                "transaction_id": tx.id,
                "amount_paise": tx.amount_paise,
                "score": risk_result.score,
                "band": risk_result.band
            }),
            related_transaction_id=tx.id,
            dedupe_key=f"held_tx_{tx.id}",
            created_at=created_at
        )
        db.add(alert)

        # Audit event
        db.add(AuditLog(
            actor_id=user.id,
            entity_type="Transaction",
            entity_id=tx.id,
            action="payment_held_for_review",
            safe_metadata_json=json.dumps({"score": risk_result.score, "band": risk_result.band}),
            created_at=created_at
        ))

    db.commit()

    # Format response
    response_data = {
        "id": tx.id,
        "user_id": tx.user_id,
        "type": tx.type,
        "source": tx.source,
        "amount_paise": tx.amount_paise,
        "category": tx.category,
        "payee_id": tx.payee_id,
        "payee_name": payee.display_name,
        "masked_payee": payee.masked_identifier,
        "method": tx.method,
        "status": tx.status,
        "note": tx.note,
        "created_at": tx.created_at.isoformat(),
        "assessment": {
            "score": risk_result.score,
            "band": risk_result.band,
            "rules_version": risk_result.rules_version,
            "reasons": [r.to_dict() for r in risk_result.reasons]
        }
    }

    if idempotency_key and raw_payload_bytes:
        save_idempotency_record(db, user.id, idempotency_key, raw_payload_bytes, response_data)
        db.commit()

    return response_data

def confirm_payment(db: Session, user: User, payment_id: int) -> Dict[str, Any]:
    """
    Customer explicitly confirms a Medium risk payment (§9):
    1. Validates status is awaiting_confirmation
    2. Atomically re-checks available_balance (if insufficient -> 409 INSUFFICIENT_FUNDS, remains awaiting_confirmation)
    3. DOES NOT re-score
    4. Transitions to completed
    5. Creates post_review case
    6. Moves payee to known
    """
    tx = db.query(Transaction).filter(
        Transaction.id == payment_id,
        Transaction.user_id == user.id
    ).with_for_update().first()

    if not tx:
        raise AppError("NOT_FOUND", "Payment not found", status_code=404)

    # Idempotent confirmation if already completed
    if tx.status == "completed":
        return {"id": tx.id, "status": "completed", "message": "Payment already confirmed"}

    validate_transition(tx.status, "completed")

    # Atomic funds check
    balances = get_ledger_balances(db, user.id)
    if tx.amount_paise > balances["available_balance_paise"]:
        raise AppError(
            code="INSUFFICIENT_FUNDS",
            message="Insufficient available funds to complete confirmation.",
            status_code=409,
            params={
                "amount_paise": tx.amount_paise,
                "available_paise": balances["available_balance_paise"]
            }
        )

    # Complete payment
    tx.status = "completed"

    # Move payee to known if new
    if tx.payee and tx.payee.trust_status == "new":
        tx.payee.trust_status = "known"

    # Create post_review case (§9)
    post_case = ReviewCase(
        transaction_id=tx.id,
        case_type="post_review",
        status="open",
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(post_case)

    # Audit confirmation
    db.add(AuditLog(
        actor_id=user.id,
        entity_type="Transaction",
        entity_id=tx.id,
        action="medium_payment_confirmed_by_user",
        safe_metadata_json=json.dumps({"amount_paise": tx.amount_paise}),
        created_at=datetime.now(timezone.utc)
    ))

    db.commit()
    return {"id": tx.id, "status": "completed", "message": "Payment confirmed and completed successfully"}

def cancel_payment(db: Session, user: User, payment_id: int) -> Dict[str, Any]:
    """
    Customer cancels an awaiting_confirmation payment (§9):
    1. Validates status is awaiting_confirmation
    2. Transitions to cancelled
    3. Audited; creates no case
    """
    tx = db.query(Transaction).filter(
        Transaction.id == payment_id,
        Transaction.user_id == user.id
    ).with_for_update().first()

    if not tx:
        raise AppError("NOT_FOUND", "Payment not found", status_code=404)

    # Idempotent cancel if already cancelled
    if tx.status == "cancelled":
        return {"id": tx.id, "status": "cancelled", "message": "Payment already cancelled"}

    validate_transition(tx.status, "cancelled")

    tx.status = "cancelled"

    # Audit cancellation
    db.add(AuditLog(
        actor_id=user.id,
        entity_type="Transaction",
        entity_id=tx.id,
        action="medium_payment_cancelled_by_user",
        safe_metadata_json=json.dumps({"amount_paise": tx.amount_paise}),
        created_at=datetime.now(timezone.utc)
    ))

    db.commit()
    return {"id": tx.id, "status": "cancelled", "message": "Payment cancelled"}
