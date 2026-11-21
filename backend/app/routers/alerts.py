import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import User
from app.security.auth import get_current_user
from app.schemas.alerts import AlertResponse, AlertListResponse
from app.services.alert_service import get_user_alerts, mark_alert_read

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=AlertListResponse)
def list_alerts(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alerts = get_user_alerts(db, current_user.id, unread_only=unread_only)
    unread_count = sum(1 for a in alerts if a.read_at is None)

    items = []
    for a in alerts:
        try:
            params = json.loads(a.params_json) if a.params_json else {}
        except Exception:
            params = {}
        items.append({
            "id": a.id,
            "user_id": a.user_id,
            "type": a.type,
            "title_code": a.title_code,
            "params": params,
            "related_transaction_id": a.related_transaction_id,
            "read_at": a.read_at.isoformat() if a.read_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else ""
        })

    return {
        "items": items,
        "unread_count": unread_count
    }

@router.post("/{alert_id}/read", response_model=AlertResponse)
def mark_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alert = mark_alert_read(db, alert_id, current_user.id)
    try:
        params = json.loads(alert.params_json) if alert.params_json else {}
    except Exception:
        params = {}
    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "type": alert.type,
        "title_code": alert.title_code,
        "params": params,
        "related_transaction_id": alert.related_transaction_id,
        "read_at": alert.read_at.isoformat() if alert.read_at else None,
        "created_at": alert.created_at.isoformat() if alert.created_at else ""
    }
