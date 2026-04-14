from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from ...core.database import get_db
from ...models.code_change import CodeChange
from ...schemas.code_change import CodeChangeCreate, CodeChangeResponse

router = APIRouter(prefix="/code-changes", tags=["code-changes"])


@router.post("/", response_model=CodeChangeResponse, status_code=status.HTTP_201_CREATED)
async def create_code_change(
    code_change: CodeChangeCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建代码变更记录"""
    db_code_change = CodeChange(
        id=str(uuid.uuid4()),
        requirement_id=code_change.requirement_id,
        change_type=code_change.change_type or "manual",
        git_url=code_change.git_url,
        commit_hash=code_change.commit_hash,
        diff_content=code_change.diff_content,
    )
    db.add(db_code_change)
    await db.commit()
    await db.refresh(db_code_change)
    return db_code_change


@router.get("/", response_model=List[CodeChangeResponse])
async def list_code_changes(
    requirement_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取需求下的代码变更列表"""
    result = await db.execute(
        select(CodeChange)
        .where(CodeChange.requirement_id == requirement_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{code_change_id}", response_model=CodeChangeResponse)
async def get_code_change(code_change_id: str, db: AsyncSession = Depends(get_db)):
    """获取代码变更详情"""
    result = await db.execute(select(CodeChange).where(CodeChange.id == code_change_id))
    code_change = result.scalar_one_or_none()
    if not code_change:
        raise HTTPException(status_code=404, detail="Code change not found")
    return code_change


@router.delete("/{code_change_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_code_change(code_change_id: str, db: AsyncSession = Depends(get_db)):
    """删除代码变更记录"""
    result = await db.execute(select(CodeChange).where(CodeChange.id == code_change_id))
    code_change = result.scalar_one_or_none()
    if not code_change:
        raise HTTPException(status_code=404, detail="Code change not found")

    await db.delete(code_change)
    await db.commit()
