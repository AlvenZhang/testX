"""移动端执行相关 Pydantic schemas"""
from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class MobileExecutionRequest(BaseModel):
    """移动端执行请求"""
    code_content: str = Field(..., description="Appium 测试代码 (Python)")
    device_id: str = Field(..., description="设备ID")
    platform: str = Field(..., description="平台类型: android/ios")
    test_type: str = Field(default="functional", description="测试类型: functional/performance/ui")


class MobileExecutionBase(BaseModel):
    """移动端执行基础 schema"""
    device_id: str
    platform: str
    test_type: str = "functional"
    code_content: str


class MobileExecutionCreate(MobileExecutionBase):
    """创建移动端执行"""
    pass


class MobileExecutionResponse(BaseModel):
    """移动端执行响应"""
    id: str
    run_id: str
    device_id: str
    platform: str
    test_type: str
    status: str
    exit_code: int
    logs: str
    duration_ms: int
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    devices: List[Dict]
    total: int


class MobileExecutionStatusResponse(BaseModel):
    """执行状态响应"""
    run_id: str
    status: str
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class MobileExecutionLogsResponse(BaseModel):
    """执行日志响应"""
    run_id: str
    logs: str
    status: Optional[str] = None
