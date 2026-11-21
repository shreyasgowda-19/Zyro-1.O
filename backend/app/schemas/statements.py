from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, conint, conlist, constr


class StatementRequestCreate(BaseModel):
    start_date: date
    end_date: date


class StatementDecision(BaseModel):
    decision: constr(strict=True, regex=r"^(approved|rejected)$")
    note: constr(strict=True, min_length=5, max_length=500)


class StatementRequestResponse(BaseModel):
    id: int
    user_id: int
    requester_username: Optional[str] = None
    start_date: date
    end_date: date
    status: str
    requested_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by_id: Optional[int] = None
    review_note: Optional[str] = None
    transaction_count: int = 0


class ImportedTransaction(BaseModel):
    type: constr(strict=True, regex=r"^(income|expense)$")
    amount_paise: conint(strict=True, gt=0, le=1000000000000)
    category: constr(strict=True, min_length=1, max_length=50)
    note: Optional[constr(strict=True, max_length=140)] = None
    created_at: datetime
    row_number: conint(strict=True, ge=1, le=1000)


class StatementImportRequest(BaseModel):
    file_hash: constr(strict=True, regex=r"^[a-f0-9]{64}$")
    rows: conlist(ImportedTransaction, min_items=1, max_items=500)


class StatementImportResponse(BaseModel):
    imported_count: int
    duplicates_skipped: int
    transaction_ids: List[int] = Field(default_factory=list)


class StatementPreviewRow(BaseModel):
    transaction_date: datetime
    type: str
    category: str
    description: str
    amount_paise: int
    source: str


class StatementPreviewResponse(BaseModel):
    request_id: int
    total_count: int
    rows: List[StatementPreviewRow]
