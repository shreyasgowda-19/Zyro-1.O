from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, constr, conint, Field

class ReviewDecisionRequest(BaseModel):
    action: constr(strict=True) = Field(..., description="approve, reject, escalate, mark_false_alarm, mark_confirmed_fraud")
    note: constr(min_length=5, max_length=500, strict=True) = Field(..., description="Mandatory decision note (5-500 chars)")
    expected_version: conint(ge=1, strict=True) = Field(..., description="Current version of the review case for optimistic locking")

class ReviewActionResponse(BaseModel):
    id: int
    case_id: int
    actor_id: int
    actor_username: str
    actor_role: str
    action: str
    note: str
    created_at: str

class ReviewCaseResponse(BaseModel):
    id: int
    transaction_id: int
    case_type: str
    status: str
    decision: Optional[str] = None
    version: int
    assigned_reviewer_id: Optional[int] = None
    created_at: str
    updated_at: str
    masked_customer_ref: str
    amount_paise: int
    masked_payee: str
    score: int
    band: str
    reasons: List[Dict[str, Any]]
    transaction_status: str
    category: Optional[str] = None
    method: Optional[str] = None
    features_json: Optional[str] = None
    actions: Optional[List[ReviewActionResponse]] = None

class ReviewQueueResponse(BaseModel):
    items: List[ReviewCaseResponse]
    total: int
    limit: int
    offset: int

class AuditLogEntryResponse(BaseModel):
    id: int
    actor_id: Optional[int]
    actor_username: Optional[str]
    actor_role: Optional[str]
    entity_type: str
    entity_id: int
    action: str
    safe_metadata: Dict[str, Any]
    created_at: str

class AuditLogListResponse(BaseModel):
    items: List[AuditLogEntryResponse]
    total: int
    limit: int
    offset: int
