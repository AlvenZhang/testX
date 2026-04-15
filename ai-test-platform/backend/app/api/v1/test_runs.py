from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from ...core.database import get_db
from ...models.test_run import TestRun
from ...schemas.test_run import TestRunCreate, TestRunUpdate, TestRunResponse

router = APIRouter(prefix="/test-runs", tags=["test-runs"])


@router.post("/", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_test_run(
    test_run: TestRunCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试运行记录"""
    db_run = TestRun(
        id=str(uuid.uuid4()),
        project_id=test_run.project_id,
        test_code_id=test_run.test_code_id,
        status=test_run.status or "pending",
    )
    db.add(db_run)
    await db.commit()
    await db.refresh(db_run)
    return db_run


@router.get("/", response_model=List[TestRunResponse])
async def list_test_runs(
    project_id: str = None,
    requirement_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取测试运行记录列表"""
    query = select(TestRun)

    if project_id:
        query = query.where(TestRun.project_id == project_id)

    if requirement_id:
        # 通过 test_code 表关联 requirement_id
        from ...models.test_code import TestCode
        query = query.join(TestCode, TestRun.test_code_id == TestCode.id).where(
            TestCode.requirement_id == requirement_id
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(test_run_id: str, db: AsyncSession = Depends(get_db)):
    """获取测试运行记录详情"""
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    test_run = result.scalar_one_or_none()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return test_run


@router.put("/{test_run_id}", response_model=TestRunResponse)
async def update_test_run(
    test_run_id: str,
    test_run: TestRunUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新测试运行记录"""
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    db_run = result.scalar_one_or_none()
    if not db_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    update_data = test_run.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_run, key, value)

    await db.commit()
    await db.refresh(db_run)
    return db_run


@router.delete("/{test_run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_run(test_run_id: str, db: AsyncSession = Depends(get_db)):
    """删除测试运行记录"""
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    test_run = result.scalar_one_or_none()
    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    await db.delete(test_run)
    await db.commit()
