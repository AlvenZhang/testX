from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from ...core.database import get_db
from ...models.test_case import TestCase
from ...schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse

router = APIRouter(prefix="/test-cases", tags=["test-cases"])


@router.post("/", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    test_case: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试用例"""
    # 检查 case_id 是否已存在
    result = await db.execute(select(TestCase).where(TestCase.case_id == test_case.case_id))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Case ID '{test_case.case_id}' already exists")

    db_case = TestCase(
        id=str(uuid.uuid4()),
        requirement_id=test_case.requirement_id,
        case_id=test_case.case_id,
        title=test_case.title,
        steps=test_case.steps,
        expected_result=test_case.expected_result,
        priority=test_case.priority or "medium",
        status=test_case.status or "active",
    )
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.get("/", response_model=List[TestCaseResponse])
async def list_test_cases(
    requirement_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取需求下的测试用例列表"""
    result = await db.execute(
        select(TestCase)
        .where(TestCase.requirement_id == requirement_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(test_case_id: str, db: AsyncSession = Depends(get_db)):
    """获取测试用例详情"""
    result = await db.execute(select(TestCase).where(TestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case


@router.put("/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: str,
    test_case: TestCaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新测试用例"""
    result = await db.execute(select(TestCase).where(TestCase.id == test_case_id))
    db_case = result.scalar_one_or_none()
    if not db_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    update_data = test_case.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_case, key, value)

    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.delete("/{test_case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(test_case_id: str, db: AsyncSession = Depends(get_db)):
    """删除测试用例"""
    result = await db.execute(select(TestCase).where(TestCase.id == test_case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    await db.delete(test_case)
    await db.commit()
