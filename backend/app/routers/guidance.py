from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import GuidanceItem, User
from app.security.auth import get_current_user
from app.schemas.guidance import GuidanceItemResponse, ScamCheckRequest, ScamCheckResponse
from app.services.scam_checker_service import check_message_for_scam

router = APIRouter(prefix="/guidance", tags=["Guidance"])

@router.get("", response_model=List[GuidanceItemResponse])
def get_guidance_items(
    lang: str = Query("en", pattern="^(en|hi)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = db.query(GuidanceItem).filter(GuidanceItem.language == lang).all()
    # Fallback to English if no items in requested language
    if not items and lang != "en":
        items = db.query(GuidanceItem).filter(GuidanceItem.language == "en").all()
    return items

@router.post("/scam-check", response_model=ScamCheckResponse)
def scan_scam_message(
    payload: ScamCheckRequest,
    current_user: User = Depends(get_current_user)
):
    # Evaluates text deterministically without saving or logging
    result = check_message_for_scam(payload.message)
    return result
