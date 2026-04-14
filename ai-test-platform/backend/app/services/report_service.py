"""报告生成服务"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.report import Report
from ..core.database import async_session


class ReportService:
    """报告生成服务"""

    async def create_report(
        self,
        test_run_id: str,
        total_cases: int,
        passed_cases: int,
        failed_cases: int,
        duration_ms: int,
        report_type: str = "new_feature",
        log_content: Optional[str] = None,
        screenshots: Optional[List[str]] = None,
        report_data: Optional[Dict[str, Any]] = None,
    ) -> Report:
        """创建测试报告"""
        from uuid import uuid4

        async with async_session() as session:
            report = Report(
                id=str(uuid4()),
                test_run_id=test_run_id,
                total_cases=total_cases,
                passed_cases=passed_cases,
                failed_cases=failed_cases,
                duration_ms=duration_ms,
                report_type=report_type,
                log_content=log_content,
                screenshots=json.dumps(screenshots or []) if screenshots else None,
                report_data=report_data,
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return report

    async def get_report(self, report_id: str) -> Optional[Report]:
        """获取报告"""
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            return result.scalar_one_or_none()

    async def list_reports(
        self,
        test_run_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Report]:
        """列出报告"""
        async with async_session() as session:
            from sqlalchemy import select
            query = select(Report)
            if test_run_id:
                query = query.where(Report.test_run_id == test_run_id)
            query = query.offset(offset).limit(limit).order_by(Report.created_at.desc())
            result = await session.execute(query)
            return list(result.scalars().all())

    async def generate_summary(self, report: Report) -> Dict[str, Any]:
        """生成报告摘要"""
        pass_rate = 0
        if report.total_cases > 0:
            pass_rate = (report.passed_cases / report.total_cases) * 100

        return {
            "report_id": report.id,
            "test_run_id": report.test_run_id,
            "total_cases": report.total_cases,
            "passed_cases": report.passed_cases,
            "failed_cases": report.failed_cases,
            "pass_rate": round(pass_rate, 2),
            "duration_ms": report.duration_ms,
            "report_type": report.report_type,
            "created_at": report.created_at.isoformat() if report.created_at else None,
        }

    async def generate_html_report(self, report: Report) -> str:
        """生成 HTML 格式报告"""
        summary = await self.generate_summary(report)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {report.id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .passed {{ color: #52c41a; }}
        .failed {{ color: #ff4d4f; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow: auto; max-height: 400px; }}
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat">
                <div class="stat-label">Total</div>
                <div class="stat-value">{summary['total_cases']}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Passed</div>
                <div class="stat-value passed">{summary['passed_cases']}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Failed</div>
                <div class="stat-value failed">{summary['failed_cases']}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Pass Rate</div>
                <div class="stat-value">{summary['pass_rate']}%</div>
            </div>
        </div>
        <p><strong>Duration:</strong> {report.duration_ms}ms</p>
        <p><strong>Type:</strong> {report.report_type}</p>
        <p><strong>Created:</strong> {summary['created_at']}</p>
    </div>
    <h2>Logs</h2>
    <pre>{report.log_content or 'No logs'}</pre>
</body>
</html>
        """
        return html

    async def generate_json_report(self, report: Report) -> str:
        """生成 JSON 格式报告"""
        summary = await self.generate_summary(report)
        summary["log_content"] = report.log_content
        summary["report_data"] = report.report_data
        return json.dumps(summary, ensure_ascii=False, indent=2)

    async def delete_report(self, report_id: str) -> bool:
        """删除报告"""
        async with async_session() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import delete
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()
            if report:
                await session.delete(report)
                await session.commit()
                return True
            return False


_report_service: Optional[ReportService] = None


def get_report_service() -> ReportService:
    """获取报告服务实例"""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service
