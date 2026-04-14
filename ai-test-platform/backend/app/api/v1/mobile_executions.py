"""移动端测试执行 API"""
from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...services.mobile_executor import MobileExecutor, DeviceInfo, get_mobile_executor

router = APIRouter(prefix="/mobile-executions", tags=["mobile-executions"])


# ==================== Pydantic Schemas ====================

class MobileExecutionRequest(BaseModel):
    """移动端执行请求"""
    code_content: str = Field(..., description="Appium 测试代码 (Python)")
    device_id: str = Field(..., description="设备ID")
    platform: str = Field(..., description="平台类型: android/ios")
    test_type: str = Field(default="functional", description="测试类型: functional/performance/ui")


class MobileExecutionResponse(BaseModel):
    """移动端执行响应"""
    run_id: str
    status: str
    exit_code: int
    logs: str
    duration_ms: int
    device_udid: str
    platform: str
    created_at: datetime


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    devices: list[dict]
    total: int


# ==================== API Endpoints ====================

@router.post("/run", response_model=MobileExecutionResponse, status_code=status.HTTP_201_CREATED)
async def run_mobile_test(
    request: MobileExecutionRequest,
    executor: MobileExecutor = Depends(get_mobile_executor)
):
    """
    执行移动端测试

    支持 Android (UiAutomator2) 和 iOS (XCUITest) 平台
    """
    run_id = str(uuid.uuid4())

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

    return MobileExecutionResponse(
        run_id=run_id,
        status=result.get("status", "error"),
        exit_code=result.get("exit_code", 1),
        logs=result.get("logs", ""),
        duration_ms=result.get("duration_ms", 0),
        device_udid=request.device_id,
        platform=request.platform,
        created_at=datetime.now()
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


@router.get("/status/{run_id}")
async def get_execution_status(run_id: str):
    """
    获取移动端测试执行状态

    注意: 移动端测试目前是同步执行，此接口主要用于查询历史记录
    """
    # TODO: 实现状态存储和查询
    return {
        "run_id": run_id,
        "status": "completed",
        "message": "Mobile execution status tracking to be implemented"
    }


@router.get("/logs/{run_id}")
async def get_execution_logs(run_id: str):
    """
    获取移动端测试执行日志
    """
    # TODO: 实现日志存储和查询
    return {
        "run_id": run_id,
        "logs": "Log retrieval to be implemented"
    }
