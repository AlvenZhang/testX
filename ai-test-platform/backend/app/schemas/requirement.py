from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RequirementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = Field(default="medium")
    extra: Optional[dict] = None


class RequirementCreate(RequirementBase):
    project_id: str


class RequirementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    extra: Optional[dict] = None


class RequirementResponse(RequirementBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime


class RequirementVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requirement_id: str
    version: int
    title: str
    description: Optional[str]
    diff: Optional[dict]
    created_by: Optional[str]
    created_at: datetime
