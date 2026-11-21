from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import User
from app.security.auth import require_role
from app.schemas.review import (
    ReviewDecisionRequest,
    ReviewCaseResponse,
    ReviewQueueResponse,
    AuditLogListResponse
)
from app.services.review_service import (
    get_review_queue,
    get_review_case_detail,
    record_case_decision,
    get_review_audit_log
)

router = APIRouter(prefix="/review", tags=["Review"])

@router.get("/cases", response_model=ReviewQueueResponse)
def list_review_cases(
    status: Optional[str] = Query(None, description="open, escalated, closed"),
    case_type: Optional[str] = Query(None, description="hold_review, post_review"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("reviewer", "supervisor")),
    db: Session = Depends(get_db)
):
    items, total = get_review_queue(db, current_user, status=status, case_type=case_type, limit=limit, offset=offset)
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/cases/{case_id}", response_model=ReviewCaseResponse)
def get_review_case(
    case_id: int,
    current_user: User = Depends(require_role("reviewer", "supervisor")),
    db: Session = Depends(get_db)
):
    return get_review_case_detail(db, case_id, current_user)

@router.post("/cases/{case_id}/decision", response_model=ReviewCaseResponse)
def decide_review_case(
    case_id: int,
    payload: ReviewDecisionRequest,
    current_user: User = Depends(require_role("reviewer", "supervisor")),
    db: Session = Depends(get_db)
):
    return record_case_decision(
        db=db,
        case_id=case_id,
        actor=current_user,
        action=payload.action,
        note=payload.note,
        expected_version=payload.expected_version
    )

@router.get("/audit", response_model=AuditLogListResponse)
def list_review_audit_logs(
    case_id: Optional[int] = Query(None, description="Filter by review case ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("reviewer", "supervisor")),
    db: Session = Depends(get_db)
):
    items, total = get_review_audit_log(db, case_id=case_id, limit=limit, offset=offset)
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }
