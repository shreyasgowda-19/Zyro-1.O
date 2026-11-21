from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AlertResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title_code: str
    params: Dict[str, Any]
    related_transaction_id: Optional[int] = None
    read_at: Optional[str] = None
    created_at: str

class AlertListResponse(BaseModel):
    items: List[AlertResponse]
    unread_count: int
