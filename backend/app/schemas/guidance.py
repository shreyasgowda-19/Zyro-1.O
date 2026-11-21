from typing import List, Optional
from pydantic import BaseModel, Field, constr

class GuidanceItemResponse(BaseModel):
    id: int
    topic: str
    language: str
    title: str
    body: str
    source_label: str
    source_url: Optional[str] = None
    last_verified: str

    class Config:
        orm_mode = True

class ScamCheckRequest(BaseModel):
    message: constr(min_length=1, max_length=1000)

class MatchedSignal(BaseModel):
    code: str
    name: str
    description: str

class ScamCheckResponse(BaseModel):
    is_suspicious: bool
    risk_level: str  # 'low', 'medium', 'high'
    matched_signals: List[MatchedSignal]
    advice_codes: List[str]
    disclaimer: str
