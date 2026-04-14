from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TestRunBase(BaseModel):
    project_id: str
    test_code_id: str
    status: Optional[str] = "pending"


class TestRunCreate(TestRunBase):
    pass


class TestRunUpdate(BaseModel):
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    container_id: Optional[str] = None


class TestRunResponse(TestRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    container_id: Optional[str] = None
    created_at: datetime
