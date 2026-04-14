from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TestCaseBase(BaseModel):
    requirement_id: str
    case_id: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    steps: Optional[str] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = Field(default="medium")
    status: Optional[str] = Field(default="active")


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    steps: Optional[str] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TestCaseResponse(TestCaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
