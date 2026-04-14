from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CodeChangeBase(BaseModel):
    requirement_id: str
    change_type: Optional[str] = "manual"
    git_url: Optional[str] = None
    commit_hash: Optional[str] = None
    diff_content: Optional[str] = None


class CodeChangeCreate(BaseModel):
    requirement_id: str
    change_type: Optional[str] = Field(default="manual")
    git_url: Optional[str] = None
    commit_hash: Optional[str] = Field(default=None, max_length=40)
    diff_content: Optional[str] = None


class CodeChangeResponse(CodeChangeBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
