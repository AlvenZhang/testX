"""测试执行 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import logging

from ...core.database import get_db
from ...models.test_run import TestRun
from ...models.test_code import TestCode
from ...schemas.test_run import TestRunCreate, TestRunUpdate
from ...services.test_executor import get_test_executor

router = APIRouter(prefix="/executions", tags=["executions"])
logger = logging.getLogger(__name__)


@router.post("/run/{test_code_id}")
async def run_test(
    test_code_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    执行测试代码
    1. 获取测试代码
    2. 创建测试运行记录
    3. 在 Docker 沙箱中执行测试
    4. 返回执行结果
    """
    logger.info(f"Received execution request for test_code: {test_code_id}")
    # 获取测试代码
    result = await db.execute(select(TestCode).where(TestCode.id == test_code_id))
    test_code = result.scalar_one_or_none()
    if not test_code:
        logger.warning(f"Test code not found: {test_code_id}")
        raise HTTPException(status_code=404, detail="Test code not found")

    logger.info(f"Executing test: project={test_code.project_id}, framework={test_code.framework}")
    # 创建测试运行记录
    run_id = str(uuid.uuid4())
    test_run = TestRun(
        id=run_id,
        project_id=test_code.project_id,
        test_code_id=test_code_id,
        status="running",
        started_at=datetime.now(),
    )
    db.add(test_run)
    await db.commit()
    await db.refresh(test_run)
    logger.info(f"Created test run record: {run_id}")

    # 执行测试
    executor = get_test_executor()
    try:
        exec_result = await executor.execute_test(
            run_id=run_id,
            code_content=test_code.code_content,
            test_type="web",
            framework=test_code.framework
        )

        # 更新运行记录
        test_run.status = exec_result["status"]
        test_run.completed_at = datetime.now()

        await db.commit()
        logger.info(f"Test run {run_id} completed: status={exec_result['status']}")

        return {
            "run_id": run_id,
            "status": exec_result["status"],
            "exit_code": exec_result.get("exit_code"),
            "logs": exec_result.get("logs", ""),
            "duration_ms": exec_result.get("duration_ms", 0),
        }
    except Exception as e:
        logger.error(f"Test run {run_id} failed: {e}", exc_info=True)
        test_run.status = "failed"
        test_run.completed_at = datetime.now()
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
