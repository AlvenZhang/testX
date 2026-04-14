"""移动端测试执行 API"""
from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.mobile_execution import MobileExecution
from ...schemas.mobile_execution import (
    MobileExecutionRequest,
    MobileExecutionResponse as MobileExecutionResponseSchema,
    DeviceListResponse,
    MobileExecutionStatusResponse,
    MobileExecutionLogsResponse,
)
from ...services.mobile_executor import MobileExecutor, DeviceInfo, get_mobile_executor

router = APIRouter(prefix="/mobile-executions", tags=["mobile-executions"])


# ==================== API Endpoints ====================

@router.post("/run", response_model=MobileExecutionResponseSchema, status_code=status.HTTP_201_CREATED)
async def run_mobile_test(
    request: MobileExecutionRequest,
    executor: MobileExecutor = Depends(get_mobile_executor),
    db: AsyncSession = Depends(get_db),
):
    """
    执行移动端测试

    支持 Android (UiAutomator2) 和 iOS (XCUITest) 平台
    """
    run_id = str(uuid.uuid4())
    execution_id = str(uuid.uuid4())
    started_at = datetime.now()

    # 创建执行记录
    db_execution = MobileExecution(
        id=execution_id,
        run_id=run_id,
        device_id=request.device_id,
        platform=request.platform,
        test_type=request.test_type,
        status="running",
        code_content=request.code_content,
        started_at=started_at,
    )
    db.add(db_execution)
    await db.commit()

    # 构建设备信息
    device = DeviceInfo(
        udid=request.device_id,
        platform=request.platform,
        name=request.device_id,  # 实际会从设备获取
        version=""
    )

    # 执行测试
    result = await executor.execute_test(
        run_id=run_id,
        code_content=request.code_content,
        device=device,
        platform=request.platform
    )

    completed_at = datetime.now()
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)

    # 更新执行记录
    db_execution.status = result.get("status", "error")
    db_execution.exit_code = result.get("exit_code", 1)
    db_execution.logs = result.get("logs", "")
    db_execution.duration_ms = duration_ms
    db_execution.result_data = result
    db_execution.completed_at = completed_at
    if result.get("status") == "error":
        db_execution.error_message = result.get("error", "")

    await db.commit()
    await db.refresh(db_execution)

    return MobileExecutionResponseSchema(
        id=execution_id,
        run_id=run_id,
        device_id=request.device_id,
        platform=request.platform,
        test_type=request.test_type,
        status=result.get("status", "error"),
        exit_code=result.get("exit_code", 1),
        logs=result.get("logs", ""),
        duration_ms=duration_ms,
        result_data=result,
        error_message=result.get("error") if result.get("status") == "error" else None,
        created_at=db_execution.created_at,
        updated_at=db_execution.updated_at,
        started_at=started_at,
        completed_at=completed_at,
    )


@router.get("/devices", response_model=DeviceListResponse)
async def list_mobile_devices(
    platform: Optional[str] = None,
    executor: MobileExecutor = Depends(get_mobile_executor)
):
    """
    获取可用移动设备列表

    支持过滤 platform: android/ios
    """
    devices = await executor.list_devices(platform=platform)

    device_list = []
    for device in devices:
        device_list.append({
            "udid": device.udid,
            "platform": device.platform,
            "name": device.name,
            "version": device.version,
            "status": device.status,
        })

    return DeviceListResponse(
        devices=device_list,
        total=len(device_list)
    )


@router.get("/status/{run_id}", response_model=MobileExecutionStatusResponse)
async def get_execution_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取移动端测试执行状态

    注意: 移动端测试目前是同步执行，此接口主要用于查询历史记录
    """
    result = await db.execute(select(MobileExecution).where(MobileExecution.run_id == run_id))
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    duration_ms = None
    if execution.started_at and execution.completed_at:
        duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
    elif execution.started_at:
        duration_ms = int((datetime.now() - execution.started_at).total_seconds() * 1000)

    return MobileExecutionStatusResponse(
        run_id=execution.run_id,
        status=execution.status,
        message=None,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        duration_ms=duration_ms,
    )


@router.get("/logs/{run_id}", response_model=MobileExecutionLogsResponse)
async def get_execution_logs(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取移动端测试执行日志
    """
    result = await db.execute(select(MobileExecution).where(MobileExecution.run_id == run_id))
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return MobileExecutionLogsResponse(
        run_id=execution.run_id,
        logs=execution.logs or "",
        status=execution.status,
    )
