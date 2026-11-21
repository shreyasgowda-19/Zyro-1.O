import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.entities import Alert
from app.clock import utcnow
from app.errors import AppError

def create_alert(
    db: Session,
    user_id: int,
    alert_type: str,
    title_code: str,
    params: Dict[str, Any],
    dedupe_key: str,
    related_transaction_id: Optional[int] = None
) -> Alert:
    """
    Creates an in-app alert with deduplication by (user_id, dedupe_key).
    If an alert with the same key already exists, returns the existing record.
    """
    existing = db.query(Alert).filter(
        Alert.user_id == user_id,
        Alert.dedupe_key == dedupe_key
    ).first()
    if existing:
        return existing

    alert = Alert(
        user_id=user_id,
        type=alert_type,
        title_code=title_code,
        params_json=json.dumps(params),
        related_transaction_id=related_transaction_id,
        dedupe_key=dedupe_key,
        created_at=utcnow()
    )
    db.add(alert)
    db.flush()
    return alert

def get_user_alerts(db: Session, user_id: int, unread_only: bool = False) -> List[Alert]:
    query = db.query(Alert).filter(Alert.user_id == user_id)
    if unread_only:
        query = query.filter(Alert.read_at.is_(None))
    return query.order_by(Alert.created_at.desc()).all()

def mark_alert_read(db: Session, alert_id: int, user_id: int) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
    if not alert:
        raise AppError("NOT_FOUND", "Alert not found", status_code=404)
    if alert.read_at is None:
        alert.read_at = utcnow()
        db.commit()
    return alert
