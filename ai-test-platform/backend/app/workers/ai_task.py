"""AI 任务异步 worker"""
import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..services.ai_service import get_ai_service
from ..services.code_fix_service import get_code_fix_service


@dataclass
class AITask:
    """AI 任务"""
    task_id: str
    task_type: str  # analyze/generate/fix
    requirement_id: Optional[str] = None
    test_code_id: Optional[str] = None
    status: str = "pending"
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AITaskWorker:
    """AI 任务 worker"""

    def __init__(self):
        self.ai_service = get_ai_service()
        self.code_fix_service = get_code_fix_service()
        self.tasks: dict[str, AITask] = {}

    async def submit_analyze_task(self, requirement_id: str, title: str, description: str) -> AITask:
        """提交需求分析任务"""
        task = AITask(
            task_id=str(uuid.uuid4()),
            task_type="analyze",
            requirement_id=requirement_id,
        )
        self.tasks[task.task_id] = task
        asyncio.create_task(self._run_analyze_task(task.task_id, title, description))
        return task

    async def submit_generate_task(self, requirement_id: str, title: str, description: str, test_types: list[str]) -> AITask:
        """提交测试生成任务"""
        task = AITask(
            task_id=str(uuid.uuid4()),
            task_type="generate",
            requirement_id=requirement_id,
        )
        self.tasks[task.task_id] = task
        asyncio.create_task(self._run_generate_task(task.task_id, title, description, test_types))
        return task

    async def submit_fix_task(self, test_code_id: str, failed_code: str, error_message: str, test_type: str) -> AITask:
        """提交代码修复任务"""
        task = AITask(
            task_id=str(uuid.uuid4()),
            task_type="fix",
            test_code_id=test_code_id,
        )
        self.tasks[task.task_id] = task
        asyncio.create_task(self._run_fix_task(task.task_id, failed_code, error_message, test_type))
        return task

    async def _run_analyze_task(self, task_id: str, title: str, description: str):
        """执行需求分析"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = "running"
        task.started_at = datetime.now()

        try:
            result = await self.ai_service.analyze_requirement(title, description)
            task.result = result
            task.status = "success"
        except Exception as e:
            task.error = str(e)
            task.status = "error"
        finally:
            task.completed_at = datetime.now()

    async def _run_generate_task(self, task_id: str, title: str, description: str, test_types: list[str]):
        """执行测试生成"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = "running"
        task.started_at = datetime.now()

        try:
            # 1. 生成测试用例
            test_cases = await self.ai_service.generate_test_cases(title, description, test_types)

            # 2. 生成测试代码
            test_code = await self.ai_service.generate_test_code(test_cases)

            task.result = {
                "test_cases": test_cases,
                "test_code": test_code,
            }
            task.status = "success"
        except Exception as e:
            task.error = str(e)
            task.status = "error"
        finally:
            task.completed_at = datetime.now()

    async def _run_fix_task(self, task_id: str, failed_code: str, error_message: str, test_type: str):
        """执行代码修复"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = "running"
        task.started_at = datetime.now()

        try:
            result = await self.code_fix_service.fix_test_code(failed_code, error_message, test_type)
            task.result = result
            task.status = "success"
        except Exception as e:
            task.error = str(e)
            task.status = "error"
        finally:
            task.completed_at = datetime.now()

    def get_task(self, task_id: str) -> Optional[AITask]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def list_tasks(self) -> list[AITask]:
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
_ai_worker: Optional[AITaskWorker] = None


def get_ai_task_worker() -> AITaskWorker:
    """获取 AI 任务 worker"""
    global _ai_worker
    if _ai_worker is None:
        _ai_worker = AITaskWorker()
    return _ai_worker


async def run_ai_task(
    task_type: str,
    **kwargs
) -> AITask:
    """快捷函数：提交并执行 AI 任务"""
    worker = get_ai_task_worker()

    if task_type == "analyze":
        return await worker.submit_analyze_task(
            kwargs["requirement_id"],
            kwargs["title"],
            kwargs["description"]
        )
    elif task_type == "generate":
        return await worker.submit_generate_task(
            kwargs["requirement_id"],
            kwargs["title"],
            kwargs["description"],
            kwargs["test_types"]
        )
    elif task_type == "fix":
        return await worker.submit_fix_task(
            kwargs["test_code_id"],
            kwargs["failed_code"],
            kwargs["error_message"],
            kwargs["test_type"]
        )
    else:
        raise ValueError(f"Unknown task type: {task_type}")
