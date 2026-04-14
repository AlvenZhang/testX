"""测试代码管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ...core.database import get_db
from ...models.test_code import TestCode
from ...schemas.test_code import TestCodeCreate, TestCodeUpdate, TestCodeResponse

router = APIRouter(prefix="/test-code", tags=["test-code"])


@router.get("/", response_model=List[TestCodeResponse])
async def list_test_code(
    project_id: str = None,
    requirement_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取测试代码列表"""
    query = select(TestCode)
    if project_id:
        query = query.where(TestCode.project_id == project_id)
    if requirement_id:
        query = query.where(TestCode.requirement_id == requirement_id)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{test_code_id}", response_model=TestCodeResponse)
async def get_test_code(test_code_id: str, db: AsyncSession = Depends(get_db)):
    """获取测试代码详情"""
    result = await db.execute(select(TestCode).where(TestCode.id == test_code_id))
    test_code = result.scalar_one_or_none()
    if not test_code:
        raise HTTPException(status_code=404, detail="Test code not found")
    return test_code
