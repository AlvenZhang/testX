from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from ...core.database import get_db
from ...models.requirement import Requirement, RequirementVersion
from ...schemas.requirement import (
    RequirementCreate, RequirementUpdate, RequirementResponse,
    RequirementVersionResponse
)

router = APIRouter(prefix="/requirements", tags=["requirements"])


def compute_diff(old: dict, new: dict) -> dict:
    """计算两个版本之间的差异"""
    diff = {}
    if old.get("title") != new.get("title"):
        diff["title_changed"] = True
    if old.get("description") != new.get("description"):
        diff["description_changed"] = True
    return diff


@router.post("/", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    requirement: RequirementCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建需求"""
    db_req = Requirement(
        id=str(uuid.uuid4()),
        project_id=requirement.project_id,
        title=requirement.title,
        description=requirement.description,
        priority=requirement.priority or "medium",
        extra=requirement.extra,
    )
    db.add(db_req)
    await db.commit()
    await db.refresh(db_req)
    return db_req


@router.get("/", response_model=List[RequirementResponse])
async def list_requirements(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取项目下的需求列表"""
    result = await db.execute(
        select(Requirement)
        .where(Requirement.project_id == project_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """获取需求详情"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: str,
    requirement: RequirementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新需求（自动创建版本历史）"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    db_req = result.scalar_one_or_none()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 保存旧版本
    old_data = {"title": db_req.title, "description": db_req.description}
    new_version = db_req.version + 1

    # 创建版本记录
    version_entry = RequirementVersion(
        id=str(uuid.uuid4()),
        requirement_id=requirement_id,
        version=db_req.version,
        title=db_req.title,
        description=db_req.description,
        diff={},
    )
    db.add(version_entry)

    # 更新需求
    update_data = requirement.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_req, key, value)
    db_req.version = new_version

    # 创建新版本（diff）
    new_data = {"title": db_req.title, "description": db_req.description}
    version_entry.diff = compute_diff(old_data, new_data)

    await db.commit()
    await db.refresh(db_req)
    return db_req


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """删除需求"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    await db.delete(requirement)
    await db.commit()


@router.get("/{requirement_id}/versions", response_model=List[RequirementVersionResponse])
async def get_requirement_versions(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """获取需求版本历史"""
    result = await db.execute(
        select(RequirementVersion)
        .where(RequirementVersion.requirement_id == requirement_id)
        .order_by(RequirementVersion.version.desc())
    )
    return result.scalars().all()
