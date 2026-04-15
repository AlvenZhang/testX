"""测试执行 API"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import json
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


@router.post("/run-stream/{test_code_id}")
async def run_test_stream(
    test_code_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    流式执行测试代码 - 通过 SSE 流式返回执行进度
    """
    async def event_generator():
        logger.info(f"Received streaming execution request for test_code: {test_code_id}")
        try:
            # 1. 获取测试代码
            result = await db.execute(select(TestCode).where(TestCode.id == test_code_id))
            test_code = result.scalar_one_or_none()
            if not test_code:
                logger.warning(f"Test code not found: {test_code_id}")
                yield f"data: {json.dumps({'type': 'error', 'content': 'Test code not found'})}\n\n"
                return

            # 2. 创建测试运行记录
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
            logger.info(f"Created test run record: {run_id}")

            yield f"data: {json.dumps({'type': 'progress', 'content': '📋 Step 1/6: 初始化执行环境...'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'content': f'项目ID: {test_code.project_id}'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'content': f'框架: {test_code.framework}'})}\n\n"

            # 3. 执行测试
            executor = get_test_executor()
            yield f"data: {json.dumps({'type': 'progress', 'content': '🐳 Step 2/6: 创建 Docker 沙箱容器...'})}\n\n"

            try:
                exec_result = await executor.execute_test(
                    run_id=run_id,
                    code_content=test_code.code_content,
                    test_type="web",
                    framework=test_code.framework
                )
            except Exception as e:
                logger.error(f"[{run_id}] Execution error: {e}", exc_info=True)
                test_run.status = "failed"
                test_run.completed_at = datetime.now()
                await db.commit()
                yield f"data: {json.dumps({'type': 'error', 'content': f'执行失败: {str(e)}'})}\n\n"
                return

            # 4. 返回结果
            status = exec_result.get("status", "unknown")
            logs = exec_result.get("logs", "")
            duration = exec_result.get("duration_ms", 0)
            exit_code = exec_result.get("exit_code", -1)

            yield f"data: {json.dumps({'type': 'progress', 'content': f'✅ Step 3/6: 执行完成, 耗时 {duration}ms'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'content': f'📊 退出码: {exit_code}'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'content': f'📊 状态: {status}'})}\n\n"

            # 更新运行记录
            test_run.status = status
            test_run.completed_at = datetime.now()
            await db.commit()

            # 流式返回日志
            yield f"data: {json.dumps({'type': 'progress', 'content': '📋 Step 4/6: 执行日志:'})}\n\n"
            if logs:
                for line in logs.split('\n'):
                    if line.strip():
                        yield f"data: {json.dumps({'type': 'log', 'content': line})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'log', 'content': '(无日志输出)'})}\n\n"

            # 最终结果
            yield f"data: {json.dumps({'type': 'done', 'status': status, 'exit_code': exit_code, 'duration_ms': duration, 'logs': logs})}\n\n"

        except Exception as e:
            logger.error(f"Streaming execution error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
