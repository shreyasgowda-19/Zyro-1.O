import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.models.entities import ReviewCase, ReviewCaseAction, AuditLog, Transaction, Payee, RiskAssessment, RiskReason, User
from app.services.credential_guard import validate_sensitive_input
from app.services.payment_service import validate_transition
from app.services.alert_service import create_alert
from app.security.auth import mask_customer_reference
from app.clock import utcnow
from app.errors import AppError

def format_case_dto(case: ReviewCase, include_actions: bool = False, include_features: bool = False) -> Dict[str, Any]:
    tx = case.transaction
    assessment = tx.assessment if tx else None
    payee = tx.payee if tx else None

    reasons = []
    if assessment and assessment.reasons:
        for r in assessment.reasons:
            try:
                params = json.loads(r.params_json) if r.params_json else {}
            except Exception:
                params = {}
            reasons.append({
                "rule_code": r.rule_code,
                "points": r.points,
                "params": params
            })

    dto = {
        "id": case.id,
        "transaction_id": case.transaction_id,
        "case_type": case.case_type,
        "status": case.status,
        "decision": case.decision,
        "version": case.version,
        "assigned_reviewer_id": case.assigned_reviewer_id,
        "created_at": case.created_at.isoformat() if case.created_at else "",
        "updated_at": case.updated_at.isoformat() if case.updated_at else "",
        "masked_customer_ref": mask_customer_reference(tx.user_id) if tx else "CUST-UNKNOWN",
        "amount_paise": tx.amount_paise if tx else 0,
        "masked_payee": payee.masked_identifier if payee else "••••0000",
        "score": assessment.score if assessment else 0,
        "band": assessment.band if assessment else "unknown",
        "reasons": reasons,
        "transaction_status": tx.status if tx else "unknown",
        "category": tx.category if tx else None,
        "method": tx.method if tx else None,
    }

    if include_features:
        dto["features_json"] = assessment.features_json if assessment else "{}"

    if include_actions:
        actions_list = []
        if case.actions:
            for act in sorted(case.actions, key=lambda a: a.created_at):
                actions_list.append({
                    "id": act.id,
                    "case_id": act.case_id,
                    "actor_id": act.actor_id,
                    "actor_username": act.actor.username if act.actor else "unknown",
                    "actor_role": act.actor.role if act.actor else "unknown",
                    "action": act.action,
                    "note": act.note,
                    "created_at": act.created_at.isoformat() if act.created_at else ""
                })
        dto["actions"] = actions_list

    return dto

def get_review_queue(
    db: Session,
    user: User,
    status: Optional[str] = None,
    case_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Review Queue:
    Sorted by highest score DESC, then oldest created_at ASC; paginated.
    Supervisors see escalated cases. Normal reviewers only see open/closed unless granted supervisor.
    """
    query = db.query(ReviewCase).join(Transaction).outerjoin(RiskAssessment)

    if status:
        if status == "escalated" and user.role != "supervisor":
            raise AppError("FORBIDDEN", "Only supervisors can view the escalated queue", status_code=403)
        query = query.filter(ReviewCase.status == status)
    else:
        # Default queue view
        if user.role == "supervisor":
            query = query.filter(ReviewCase.status.in_(["open", "escalated"]))
        else:
            query = query.filter(ReviewCase.status == "open")

    if case_type:
        query = query.filter(ReviewCase.case_type == case_type)

    total = query.count()

    cases = query.order_by(
        desc(RiskAssessment.score),
        asc(ReviewCase.created_at)
    ).offset(offset).limit(limit).all()

    items = [format_case_dto(c) for c in cases]
    return items, total

def get_review_case_detail(db: Session, case_id: int, user: User) -> Dict[str, Any]:
    case = db.query(ReviewCase).filter(ReviewCase.id == case_id).first()
    if not case:
        raise AppError("NOT_FOUND", "Review case not found", status_code=404)
    return format_case_dto(case, include_actions=True, include_features=True)

def record_case_decision(
    db: Session,
    case_id: int,
    actor: User,
    action: str,
    note: str,
    expected_version: int
) -> Dict[str, Any]:
    """
    Records a reviewer or supervisor action on a ReviewCase.
    Enforces separation of duties, mandatory notes, optimistic locking, and atomic state updates.
    """
    case = db.query(ReviewCase).filter(ReviewCase.id == case_id).first()
    if not case:
        raise AppError("NOT_FOUND", "Review case not found", status_code=404)

    tx = case.transaction
    if not tx:
        raise AppError("NOT_FOUND", "Associated transaction not found", status_code=404)

    # 1. Self-Review Check (§6)
    if tx.user_id == actor.id:
        raise AppError("FORBIDDEN", "Reviewers cannot act on payments belonging to their own account", status_code=403)

    # 2. Mandatory Note Check (§12)
    trimmed_note = (note or "").strip()
    if len(trimmed_note) < 5 or len(trimmed_note) > 500:
        raise AppError("NOTE_REQUIRED", "Review action requires a note between 5 and 500 characters", status_code=422)
    # Sensitive input guard on note
    safe_note = validate_sensitive_input(trimmed_note, "note")

    # 3. Optimistic Concurrency Check (§9, §12)
    if case.version != expected_version:
        raise AppError(
            "CASE_CONFLICT",
            f"Case has been modified (current version {case.version}, expected {expected_version})",
            status_code=409,
            params={"current_version": case.version, "expected_version": expected_version}
        )

    # 4. State & Role Validation (§6, §12)
    if case.status == "closed":
        raise AppError("ILLEGAL_TRANSITION", "Review case is already closed", status_code=400)

    now = utcnow()

    if case.status == "escalated":
        # Only supervisors can resolve escalated cases
        if actor.role != "supervisor":
            raise AppError("FORBIDDEN", "Only supervisors can resolve escalated cases", status_code=403)

        # Two-person rule: supervisor resolving cannot be the actor who escalated it (§6)
        escalation_actions = db.query(ReviewCaseAction).filter(
            ReviewCaseAction.case_id == case.id,
            ReviewCaseAction.action == "escalate"
        ).all()
        for ea in escalation_actions:
            if ea.actor_id == actor.id:
                raise AppError(
                    "FORBIDDEN",
                    "Two-person rule violation: the supervisor resolving an escalation cannot be the reviewer who escalated it",
                    status_code=403
                )

        if case.case_type == "hold_review":
            allowed_actions = ["approve", "reject"]
        else:
            allowed_actions = ["mark_false_alarm", "mark_confirmed_fraud"]

        if action not in allowed_actions:
            raise AppError("ILLEGAL_TRANSITION", f"Invalid action '{action}' for escalated {case.case_type}", status_code=400)

    elif case.status == "open":
        if case.case_type == "hold_review":
            allowed_actions = ["approve", "reject", "escalate"]
        else:
            allowed_actions = ["mark_false_alarm", "mark_confirmed_fraud", "escalate"]

        if action not in allowed_actions:
            raise AppError("ILLEGAL_TRANSITION", f"Invalid action '{action}' for open {case.case_type}", status_code=400)

    # 5. Apply Action Side Effects (§9, §12)
    payee = tx.payee

    if action == "approve":
        validate_transition(tx.status, "completed")
        tx.status = "completed"
        case.status = "closed"
        case.decision = "approved"
        # First completed payment moves payee new -> known
        if payee and payee.trust_status == "new":
            payee.trust_status = "known"
        # Customer in-app alert
        create_alert(
            db,
            user_id=tx.user_id,
            alert_type="review",
            title_code="alert.review.approved",
            params={
                "transaction_id": tx.id,
                "amount_paise": tx.amount_paise,
                "payee_masked": payee.masked_identifier if payee else "••••0000"
            },
            dedupe_key=f"review_decision_{case.id}_{case.version}",
            related_transaction_id=tx.id
        )

        from app.services.budget_service import evaluate_budget_alerts
        evaluate_budget_alerts(db, tx.user_id, tx.created_at.strftime("%Y-%m"))

    elif action == "reject":
        validate_transition(tx.status, "released")
        tx.status = "released"
        case.status = "closed"
        case.decision = "rejected"
        # Customer in-app alert
        create_alert(
            db,
            user_id=tx.user_id,
            alert_type="review",
            title_code="alert.review.rejected",
            params={
                "transaction_id": tx.id,
                "amount_paise": tx.amount_paise,
                "payee_masked": payee.masked_identifier if payee else "••••0000"
            },
            dedupe_key=f"review_decision_{case.id}_{case.version}",
            related_transaction_id=tx.id
        )

    elif action == "escalate":
        # Hold-review escalations change the payment state because funds are
        # still reserved. Post-review cases concern completed payments, so
        # escalate only the case and leave the completed ledger entry intact.
        if case.case_type == "hold_review":
            validate_transition(tx.status, "escalated")
            tx.status = "escalated"
        elif tx.status != "completed":
            raise AppError(
                "ILLEGAL_TRANSITION",
                f"Cannot escalate a post-review case while its transaction is '{tx.status}'.",
                status_code=400
            )
        case.status = "escalated"
        case.assigned_reviewer_id = actor.id

    elif action == "mark_confirmed_fraud":
        case.status = "closed"
        case.decision = "confirmed_fraud"
        if payee:
            payee.trust_status = "flagged"
        create_alert(
            db,
            user_id=tx.user_id,
            alert_type="fraud",
            title_code="alert.fraud.confirmed_fraud",
            params={
                "transaction_id": tx.id,
                "payee_masked": payee.masked_identifier if payee else "••••0000"
            },
            dedupe_key=f"fraud_confirmed_{case.id}_{case.version}",
            related_transaction_id=tx.id
        )

    elif action == "mark_false_alarm":
        case.status = "closed"
        case.decision = "false_alarm"
        create_alert(
            db,
            user_id=tx.user_id,
            alert_type="review",
            title_code="alert.review.false_alarm",
            params={"transaction_id": tx.id},
            dedupe_key=f"false_alarm_{case.id}_{case.version}",
            related_transaction_id=tx.id
        )

    # 6. Increment Version & Save Action
    case.version += 1
    case.updated_at = now

    action_record = ReviewCaseAction(
        case_id=case.id,
        actor_id=actor.id,
        action=action,
        note=safe_note,
        created_at=now
    )
    db.add(action_record)

    # 7. Safe Metadata Audit Log
    audit_record = AuditLog(
        actor_id=actor.id,
        entity_type="review_case",
        entity_id=case.id,
        action=action,
        safe_metadata_json=json.dumps({
            "action": action,
            "old_version": expected_version,
            "new_version": case.version,
            "case_type": case.case_type,
            "decision": case.decision,
            "actor_role": actor.role
        }),
        created_at=now
    )
    db.add(audit_record)

    db.commit()
    db.refresh(case)

    return format_case_dto(case, include_actions=True, include_features=True)

def get_review_audit_log(
    db: Session,
    case_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    query = db.query(AuditLog).outerjoin(User, AuditLog.actor_id == User.id)

    if case_id is not None:
        query = query.filter(AuditLog.entity_type == "review_case", AuditLog.entity_id == case_id)
    else:
        # Show review-relevant audit events (§12)
        query = query.filter(AuditLog.entity_type.in_(["review_case", "ReviewCase", "Transaction", "transaction"]))

    total = query.count()
    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    items = []
    for log in logs:
        try:
            metadata = json.loads(log.safe_metadata_json) if log.safe_metadata_json else {}
        except Exception:
            metadata = {}
        items.append({
            "id": log.id,
            "actor_id": log.actor_id,
            "actor_username": log.actor.username if log.actor else "system",
            "actor_role": log.actor.role if log.actor else None,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "safe_metadata": metadata,
            "created_at": log.created_at.isoformat() if log.created_at else ""
        })

    return items, total
