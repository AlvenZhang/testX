from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from ...core.database import get_db
from ...models.test_plan import TestPlan
from ...schemas.test_plan import TestPlanCreate, TestPlanUpdate, TestPlanResponse

router = APIRouter(prefix="/test-plans", tags=["test-plans"])


@router.post("/", response_model=TestPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_test_plan(
    test_plan: TestPlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试方案"""
    db_plan = TestPlan(
        id=str(uuid.uuid4()),
        requirement_id=test_plan.requirement_id,
        test_scope=test_plan.test_scope,
        test_types=test_plan.test_types,
        test_strategy=test_plan.test_strategy,
        risk_points=test_plan.risk_points,
    )
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan


@router.get("/", response_model=List[TestPlanResponse])
async def list_test_plans(
    requirement_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取需求下的测试方案列表"""
    result = await db.execute(
        select(TestPlan)
        .where(TestPlan.requirement_id == requirement_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{test_plan_id}", response_model=TestPlanResponse)
async def get_test_plan(test_plan_id: str, db: AsyncSession = Depends(get_db)):
    """获取测试方案详情"""
    result = await db.execute(select(TestPlan).where(TestPlan.id == test_plan_id))
    test_plan = result.scalar_one_or_none()
    if not test_plan:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return test_plan


@router.put("/{test_plan_id}", response_model=TestPlanResponse)
async def update_test_plan(
    test_plan_id: str,
    test_plan: TestPlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新测试方案"""
    result = await db.execute(select(TestPlan).where(TestPlan.id == test_plan_id))
    db_plan = result.scalar_one_or_none()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Test plan not found")

    update_data = test_plan.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plan, key, value)

    await db.commit()
    await db.refresh(db_plan)
    return db_plan


@router.delete("/{test_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_plan(test_plan_id: str, db: AsyncSession = Depends(get_db)):
    """删除测试方案"""
    result = await db.execute(select(TestPlan).where(TestPlan.id == test_plan_id))
    test_plan = result.scalar_one_or_none()
    if not test_plan:
        raise HTTPException(status_code=404, detail="Test plan not found")

    await db.delete(test_plan)
    await db.commit()
