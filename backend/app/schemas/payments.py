from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, conint, constr, Field

StrictPaise = conint(ge=100, le=20000000, strict=True)
StrictOptionalStr50 = constr(max_length=50, strict=True)
StrictOptionalStr60 = constr(max_length=60, strict=True)
StrictOptionalStr140 = constr(max_length=140, strict=True)

class PaymentCreateRequest(BaseModel):
    amount_paise: StrictPaise = Field(..., description="Amount in integer paise (₹1 to ₹2,00,000)")
    category: Optional[StrictOptionalStr50] = "General"
    payee_id: Optional[conint(strict=True)] = None
    payee_display_name: Optional[StrictOptionalStr60] = None
    payee_masked_identifier: Optional[constr(max_length=30, strict=True)] = None
    method: constr(max_length=30, strict=True) = "upi"
    note: Optional[StrictOptionalStr140] = None
    synthetic_device_tag: Optional[StrictOptionalStr50] = None
    synthetic_city_tag: Optional[StrictOptionalStr50] = None
    simulated_at: Optional[datetime] = None

class RiskReasonResponse(BaseModel):
    rule_code: str
    points: int
    params: Dict[str, Any]

class RiskAssessmentResponse(BaseModel):
    score: int
    band: str
    rules_version: str
    reasons: List[RiskReasonResponse]

class PaymentResponse(BaseModel):
    id: int
    user_id: int
    type: str
    source: str
    amount_paise: int
    category: str
    payee_id: Optional[int] = None
    payee_name: Optional[str] = None
    masked_payee: Optional[str] = None
    method: str
    status: str
    note: Optional[str] = None
    created_at: str
    assessment: Optional[RiskAssessmentResponse] = None

class ManualTransactionCreateRequest(BaseModel):
    type: constr(strict=True) = Field(..., description="income or expense")
    amount_paise: StrictPaise = Field(...)
    category: constr(max_length=50, strict=True) = Field(...)
    note: Optional[StrictOptionalStr140] = None
    created_at: Optional[datetime] = None

class CategoryPatchRequest(BaseModel):
    category: constr(min_length=1, max_length=50, strict=True) = Field(...)

class ReconciliationResponse(BaseModel):
    all_passed: bool
    timestamp: Optional[str] = None
    checks: List[Dict[str, Any]]
    balances: Dict[str, int]

class BalancesResponse(BaseModel):
    opening_balance_paise: int
    completed_income_paise: int
    completed_expenses_paise: int
    completed_balance_paise: int
    held_balance_paise: int
    available_balance_paise: int
