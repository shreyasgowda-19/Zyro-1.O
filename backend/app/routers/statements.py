import csv
import hashlib
import io
import json
from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.clock import utcnow
from app.database import get_db
from app.errors import AppError
from app.models.entities import AuditLog, StatementRequest, Transaction, User
from app.schemas.statements import (
    StatementDecision,
    StatementImportRequest,
    StatementImportResponse,
    StatementRequestCreate,
    StatementRequestResponse,
    StatementPreviewResponse,
)
from app.security.auth import require_role
from app.services.credential_guard import validate_sensitive_input

router = APIRouter(prefix="/statements", tags=["Statements"])


def _transaction_count(db: Session, user_id: int, start_date, end_date) -> int:
    start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.status == "completed",
        Transaction.created_at >= start_at,
        Transaction.created_at < end_at,
    ).count()


def _request_payload(db: Session, request: StatementRequest, username=None):
    return {
        "id": request.id,
        "user_id": request.user_id,
        "requester_username": username,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "status": request.status,
        "requested_at": request.requested_at,
        "reviewed_at": request.reviewed_at,
        "reviewed_by_id": request.reviewed_by_id,
        "review_note": request.review_note,
        "transaction_count": _transaction_count(db, request.user_id, request.start_date, request.end_date),
    }


def _csv_cell(value: str) -> str:
    """Prevent spreadsheet formula execution when a customer opens the exported CSV."""
    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def _statement_transactions(db: Session, user_id: int, start_date, end_date):
    start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.status == "completed",
        Transaction.created_at >= start_at,
        Transaction.created_at < end_at,
    ).order_by(Transaction.created_at.asc()).all()


@router.post("/import", response_model=StatementImportResponse)
def import_statement_csv(
    payload: StatementImportRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    if len(payload.rows) > 500:
        raise AppError("VALIDATION_ERROR", "A statement import can contain at most 500 rows", status_code=422)
    row_numbers = [row.row_number for row in payload.rows]
    if len(set(row_numbers)) != len(row_numbers):
        raise AppError("VALIDATION_ERROR", "Imported statement rows must have unique row numbers", status_code=422)

    fingerprints = {
        row.row_number: hashlib.sha256(
            f"{current_user.id}:{payload.file_hash}:{row.row_number}".encode("utf-8")
        ).hexdigest()
        for row in payload.rows
    }
    existing = set(
        value[0]
        for value in db.query(Transaction.import_fingerprint).filter(
            Transaction.user_id == current_user.id,
            Transaction.import_fingerprint.in_(fingerprints.values()),
        ).all()
    )

    new_transactions = []
    imported_months = set()
    for row in payload.rows:
        fingerprint = fingerprints[row.row_number]
        if fingerprint in existing:
            continue
        safe_note = validate_sensitive_input(row.note, "note") if row.note else None
        new_transactions.append(Transaction(
            user_id=current_user.id,
            type=row.type,
            source="manual",
            amount_paise=row.amount_paise,
            category=row.category.strip(),
            method="netbanking" if row.type == "income" else "upi",
            status="completed",
            note=safe_note,
            created_at=row.created_at,
            import_fingerprint=fingerprint,
        ))
        imported_months.add(row.created_at.strftime("%Y-%m"))

    db.add_all(new_transactions)
    db.add(AuditLog(
        actor_id=current_user.id,
        entity_type="statement_import",
        entity_id=current_user.id,
        action="imported_transactions",
        safe_metadata_json=json.dumps({
            "imported_count": len(new_transactions),
            "duplicates_skipped": len(payload.rows) - len(new_transactions),
            "file_hash": payload.file_hash,
        }),
    ))
    db.commit()

    ids = [item.id for item in new_transactions]
    for month in imported_months:
        from app.services.budget_service import evaluate_budget_alerts
        evaluate_budget_alerts(db, current_user.id, month)

    return StatementImportResponse(
        imported_count=len(new_transactions),
        duplicates_skipped=len(payload.rows) - len(new_transactions),
        transaction_ids=ids,
    )


@router.post("/requests", response_model=StatementRequestResponse, status_code=status.HTTP_201_CREATED)
def create_statement_request(
    payload: StatementRequestCreate,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    today = utcnow().date()
    if payload.end_date < payload.start_date or payload.end_date > today:
        raise AppError("VALIDATION_ERROR", "Choose a valid past or current date range", status_code=422)
    if (payload.end_date - payload.start_date).days > 366:
        raise AppError("VALIDATION_ERROR", "Statement requests can cover up to 12 months", status_code=422)
    pending = db.query(StatementRequest).filter(
        StatementRequest.user_id == current_user.id,
        StatementRequest.start_date == payload.start_date,
        StatementRequest.end_date == payload.end_date,
        StatementRequest.status == "pending",
    ).first()
    if pending:
        raise AppError("CONFLICT", "A request for this date range is already pending", status_code=409)

    request = StatementRequest(
        user_id=current_user.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(request)
    db.flush()
    db.add(AuditLog(
        actor_id=current_user.id,
        entity_type="statement_request",
        entity_id=request.id,
        action="requested_statement",
        safe_metadata_json=json.dumps({"start_date": str(payload.start_date), "end_date": str(payload.end_date)}),
    ))
    db.commit()
    db.refresh(request)
    return _request_payload(db, request)


@router.get("/requests", response_model=list[StatementRequestResponse])
def list_my_statement_requests(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    requests = db.query(StatementRequest).filter(
        StatementRequest.user_id == current_user.id
    ).order_by(StatementRequest.requested_at.desc()).all()
    return [_request_payload(db, item) for item in requests]


@router.get("/requests/queue", response_model=list[StatementRequestResponse])
def list_statement_request_queue(
    current_user: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
):
    requests = db.query(StatementRequest).join(User, User.id == StatementRequest.user_id).filter(
        StatementRequest.status == "pending"
    ).order_by(StatementRequest.requested_at.asc()).all()
    return [_request_payload(db, item, db.query(User.username).filter(User.id == item.user_id).scalar()) for item in requests]


@router.post("/requests/{request_id}/decision", response_model=StatementRequestResponse)
def decide_statement_request(
    request_id: int,
    payload: StatementDecision,
    current_user: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
):
    request = db.query(StatementRequest).filter(StatementRequest.id == request_id).first()
    if not request:
        raise AppError("NOT_FOUND", "Statement request not found", status_code=404)
    if request.status != "pending":
        raise AppError("CASE_CONFLICT", "This statement request has already been decided", status_code=409)
    request.status = payload.decision
    request.reviewed_at = utcnow()
    request.reviewed_by_id = current_user.id
    request.review_note = validate_sensitive_input(payload.note.strip(), "review_note")
    db.add(AuditLog(
        actor_id=current_user.id,
        entity_type="statement_request",
        entity_id=request.id,
        action=payload.decision,
        safe_metadata_json=json.dumps({"decision": payload.decision}),
    ))
    from app.services.alert_service import create_alert
    create_alert(
        db,
        user_id=request.user_id,
        alert_type="review",
        title_code=f"alert.statement.{payload.decision}",
        params={"start_date": str(request.start_date), "end_date": str(request.end_date)},
        dedupe_key=f"statement_request_{request.id}_{payload.decision}",
    )
    db.commit()
    db.refresh(request)
    username = db.query(User.username).filter(User.id == request.user_id).scalar()
    return _request_payload(db, request, username)


@router.get("/requests/{request_id}/preview", response_model=StatementPreviewResponse)
def preview_statement_request(
    request_id: int,
    current_user: User = Depends(require_role("supervisor")),
    db: Session = Depends(get_db),
):
    request = db.query(StatementRequest).filter(StatementRequest.id == request_id).first()
    if not request:
        raise AppError("NOT_FOUND", "Statement request not found", status_code=404)
    transactions = _statement_transactions(db, request.user_id, request.start_date, request.end_date)
    return {
        "request_id": request.id,
        "total_count": len(transactions),
        "rows": [{
            "transaction_date": item.created_at,
            "type": item.type,
            "category": item.category,
            "description": item.note or "Transaction",
            "amount_paise": item.amount_paise,
            "source": "Customer entered" if item.import_fingerprint else "PayGuard recorded",
        } for item in transactions[:50]],
    }


@router.get("/requests/{request_id}/download")
def download_approved_statement(
    request_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    request = db.query(StatementRequest).filter(
        StatementRequest.id == request_id,
        StatementRequest.user_id == current_user.id,
    ).first()
    if not request:
        raise AppError("NOT_FOUND", "Statement request not found", status_code=404)
    if request.status != "approved":
        raise AppError("FORBIDDEN", "This statement is not approved for download", status_code=403)

    transactions = _statement_transactions(db, current_user.id, request.start_date, request.end_date)

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Description", "Amount INR", "Record source"])
    for transaction in transactions:
        writer.writerow([
            transaction.created_at.isoformat(),
            transaction.type,
            _csv_cell(transaction.category),
            _csv_cell(transaction.note or ""),
            f"{transaction.amount_paise / 100:.2f}",
            "Customer entered" if transaction.import_fingerprint else "PayGuard recorded",
        ])
    response = StreamingResponse(iter(["\ufeff" + output.getvalue()]), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="payguard_activity_{request.id}.csv"'
    return response
