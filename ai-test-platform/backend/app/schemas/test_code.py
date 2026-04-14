from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TestCodeBase(BaseModel):
    project_id: str
    requirement_id: Optional[str] = None
    test_case_ids: Optional[list[str]] = None
    framework: str = "pytest"
    code_content: str
    status: Optional[str] = "active"


class TestCodeCreate(TestCodeBase):
    pass


class TestCodeUpdate(BaseModel):
    code_content: Optional[str] = None
    status: Optional[str] = None


class TestCodeResponse(TestCodeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    created_at: datetime
    updated_at: datetime
