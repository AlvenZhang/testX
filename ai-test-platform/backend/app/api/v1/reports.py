from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from ...core.database import get_db
from ...models.report import Report
from ...schemas.report import ReportCreate, ReportUpdate, ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report: ReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建测试报告"""
    db_report = Report(
        id=str(uuid.uuid4()),
        test_run_id=report.test_run_id,
        total_cases=report.total_cases or 0,
        passed_cases=report.passed_cases or 0,
        failed_cases=report.failed_cases or 0,
        duration_ms=report.duration_ms or 0,
        report_type=report.report_type or "new_feature",
        report_data=report.report_data,
        log_content=report.log_content,
        screenshots=report.screenshots,
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    test_run_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取测试运行下的报告列表"""
    result = await db.execute(
        select(Report)
        .where(Report.test_run_id == test_run_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """获取报告详情"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report: ReportUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新报告"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    db_report = result.scalar_one_or_none()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")

    update_data = report.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_report, key, value)

    await db.commit()
    await db.refresh(db_report)
    return db_report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """删除报告"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.delete(report)
    await db.commit()
