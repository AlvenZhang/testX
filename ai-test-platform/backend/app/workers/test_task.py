"""测试任务异步 worker"""
import asyncio
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.test_executor import get_test_executor
from ..services.mobile_executor import get_mobile_executor
from ..core.config import get_settings
from ..core.database import async_session
from ..models.test_code import TestCode


@dataclass
class TestTask:
    """测试任务"""
    task_id: str
    test_code_id: str
    test_type: str  # api/web/mobile
    platform: Optional[str] = None  # android/ios (for mobile)
    device_id: Optional[str] = None
    status: str = "pending"
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TestTaskWorker:
    """测试任务 worker"""

    def __init__(self):
        self.executor = get_test_executor()
        self.mobile_executor = get_mobile_executor()
        self.tasks: dict[str, TestTask] = {}
        self._running = False

    async def submit_task(
        self,
        test_code_id: str,
        test_type: str,
        platform: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> TestTask:
        """提交测试任务"""
        task = TestTask(
            task_id=str(uuid.uuid4()),
            test_code_id=test_code_id,
            test_type=test_type,
            platform=platform,
            device_id=device_id,
        )
        self.tasks[task.task_id] = task

        # 异步执行
        asyncio.create_task(self._run_task(task.task_id))

        return task

    async def _run_task(self, task_id: str):
        """执行任务"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = "running"
        task.started_at = datetime.now()

        try:
            if task.test_type == "mobile":
                # 移动端测试
                from ..services.mobile_executor import DeviceInfo
                device = DeviceInfo(
                    udid=task.device_id or "",
                    platform=task.platform or "android",
                    name=task.device_id or "Unknown",
                    version=""
                )
                # 获取测试代码
                code_content = await self._get_test_code(task.test_code_id)
                result = await self.mobile_executor.execute_test(
                    run_id=task_id,
                    code_content=code_content,
                    device=device,
                    platform=task.platform or "android"
                )
            else:
                # Web/API 测试
                code_content = await self._get_test_code(task.test_code_id)
                result = await self.executor.execute_test(
                    run_id=task_id,
                    code_content=code_content,
                    test_type=task.test_type
                )

            task.result = result
            task.status = "success" if result.get("status") == "success" else "failed"

        except Exception as e:
            task.result = {"status": "error", "error": str(e)}
            task.status = "error"

        finally:
            task.completed_at = datetime.now()

    async def _get_test_code(self, test_code_id: str) -> str:
        """获取测试代码"""
        # 从数据库获取测试代码
        try:
            async with async_session() as session:
                result = await session.execute(select(TestCode).where(TestCode.id == test_code_id))
                test_code = result.scalar_one_or_none()
                if test_code:
                    return test_code.code_content or ""
                return ""
        except Exception:
            return ""

    def get_task(self, task_id: str) -> Optional[TestTask]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def list_tasks(self) -> list[TestTask]:
        """列出所有任务"""
        return list(self.tasks.values())

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status == "pending":
            task.status = "cancelled"
            task.completed_at = datetime.now()
            return True
        return False


# 全局 worker 实例
_worker: Optional[TestTaskWorker] = None


def get_test_task_worker() -> TestTaskWorker:
    """获取测试任务 worker"""
    global _worker
    if _worker is None:
        _worker = TestTaskWorker()
    return _worker


async def run_test_task(
    test_code_id: str,
    test_type: str,
    platform: Optional[str] = None,
    device_id: Optional[str] = None,
) -> TestTask:
    """快捷函数：提交并执行测试任务"""
    worker = get_test_task_worker()
    return await worker.submit_task(test_code_id, test_type, platform, device_id)
