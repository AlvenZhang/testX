from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReportBase(BaseModel):
    test_run_id: str
    total_cases: Optional[int] = 0
    passed_cases: Optional[int] = 0
    failed_cases: Optional[int] = 0
    duration_ms: Optional[int] = 0
    report_type: Optional[str] = "new_feature"
    report_data: Optional[dict] = None
    log_content: Optional[str] = None
    screenshots: Optional[list[str]] = None


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    total_cases: Optional[int] = None
    passed_cases: Optional[int] = None
    failed_cases: Optional[int] = None
    duration_ms: Optional[int] = None
    report_data: Optional[dict] = None
    log_content: Optional[str] = None
    screenshots: Optional[list[str]] = None


class ReportResponse(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
