"""报告导出 API"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import io
import csv

from ...core.database import get_db
from ...models.report import Report
from ...models.test_run import TestRun
from ...models.test_case import TestCase

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/report/{report_id}/csv")
async def export_report_csv(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """导出报告为 CSV"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # 获取测试运行
    result = await db.execute(select(TestRun).where(TestRun.id == report.test_run_id))
    test_run = result.scalar_one_or_none()

    # 创建 CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(["AI测试平台报告"])
    writer.writerow(["报告ID", report.id])
    writer.writerow(["报告类型", report.report_type])
    writer.writerow(["创建时间", report.created_at])
    writer.writerow([])
    writer.writerow(["测试结果汇总"])
    writer.writerow(["总用例数", report.total_cases])
    writer.writerow(["通过数", report.passed_cases])
    writer.writerow(["失败数", report.failed_cases])
    writer.writerow(["执行时长(ms)", report.duration_ms])
    writer.writerow([])
    writer.writerow(["日志内容"])
    writer.writerow([report.log_content or ""])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=report_{report_id}.csv"
        }
    )


@router.get("/test-cases/{project_id}/csv")
async def export_test_cases_csv(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """导出测试用例为 CSV"""
    from ...models.requirement import Requirement

    # 获取项目的需求
    result = await db.execute(select(Requirement).where(Requirement.project_id == project_id))
    requirements = result.scalars().all()

    req_ids = [r.id for r in requirements]

    # 获取测试用例
    result = await db.execute(select(TestCase).where(TestCase.requirement_id.in_(req_ids)))
    test_cases = result.scalars().all()

    # 创建 CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(["用例ID", "标题", "优先级", "状态", "步骤", "预期结果", "创建时间"])

    for case in test_cases:
        writer.writerow([
            case.case_id,
            case.title,
            case.priority,
            case.status,
            case.steps or "",
            case.expected_result or "",
            case.created_at
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=test_cases_{project_id}.csv"
        }
    )
