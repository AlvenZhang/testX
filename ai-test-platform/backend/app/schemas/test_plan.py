from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TestPlanBase(BaseModel):
    requirement_id: str
    test_scope: Optional[str] = None
    test_types: Optional[list[str]] = None
    test_strategy: Optional[str] = None
    risk_points: Optional[str] = None


class TestPlanCreate(TestPlanBase):
    pass


class TestPlanUpdate(BaseModel):
    test_scope: Optional[str] = None
    test_types: Optional[list[str]] = None
    test_strategy: Optional[str] = None
    risk_points: Optional[str] = None


class TestPlanResponse(TestPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
