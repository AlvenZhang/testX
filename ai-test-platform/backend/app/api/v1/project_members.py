"""项目成员管理 API"""
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.project_member import ProjectMember
from ...schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse

router = APIRouter(prefix="/project-members", tags=["project-members"])


@router.get("/project/{project_id}", response_model=List[ProjectMemberResponse])
async def list_project_members(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取项目成员列表"""
    result = await db.execute(select(ProjectMember).where(ProjectMember.project_id == project_id))
    return result.scalars().all()


@router.post("/", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    member: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
):
    """添加项目成员"""
    # 检查是否已存在
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == member.project_id,
            ProjectMember.user_id == member.user_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Member already exists")

    db_member = ProjectMember(
        id=str(uuid.uuid4()),
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
    )
    db.add(db_member)
    await db.commit()
    await db.refresh(db_member)
    return db_member


@router.put("/{member_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    member_id: str,
    member_update: ProjectMemberUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新项目成员角色"""
    result = await db.execute(select(ProjectMember).where(ProjectMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = member_update.role
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    member_id: str,
    db: AsyncSession = Depends(get_db),
):
    """移除项目成员"""
    result = await db.execute(select(ProjectMember).where(ProjectMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(member)
    await db.commit()
