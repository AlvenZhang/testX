from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """项目基础schema"""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    git_url: Optional[str] = None
    config: Optional[dict] = None


class ProjectCreate(ProjectBase):
    """创建项目请求"""

    pass


class ProjectUpdate(BaseModel):
    """更新项目请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    git_url: Optional[str] = None
    config: Optional[dict] = None


class ProjectResponse(ProjectBase):
    """项目响应"""

    id: str
    created_at: datetime
    updated_at: datetime
