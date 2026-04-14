"""项目成员相关 schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectMemberBase(BaseModel):
    """项目成员基础 schema"""
    role: str = Field(default="viewer", description="角色: viewer/editor/executor/admin")


class ProjectMemberCreate(ProjectMemberBase):
    """创建项目成员"""
    project_id: str
    user_id: str


class ProjectMemberUpdate(ProjectMemberBase):
    """更新项目成员"""
    pass


class ProjectMemberResponse(ProjectMemberBase):
    """项目成员响应"""
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
