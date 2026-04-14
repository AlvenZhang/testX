"""移动端执行记录模型"""
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from sqlalchemy.sql import func
from ..core.database import Base


class MobileExecution(Base):
    """移动端测试执行记录"""
    __tablename__ = "mobile_executions"

    id = Column(String(36), primary_key=True, index=True)
    run_id = Column(String(36), unique=True, index=True, nullable=False)
    device_id = Column(String(255), nullable=False)
    platform = Column(String(20), nullable=False)  # android/ios
    test_type = Column(String(50), default="functional")
    status = Column(String(20), default="pending")  # pending/running/success/failed/error
    exit_code = Column(Integer, default=0)
    logs = Column(Text, default="")
    code_content = Column(Text, default="")
    duration_ms = Column(Integer, default=0)
    result_data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
