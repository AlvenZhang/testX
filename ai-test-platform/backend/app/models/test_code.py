from sqlalchemy import Column, String, Text, JSON, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class TestCode(Base):
    __tablename__ = "test_code"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True)
    test_case_ids = Column(JSON)  # Array of case IDs
    framework = Column(Enum("pytest", "testng", "playwright", name="framework_enum"), nullable=False)
    code_content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    status = Column(Enum("active", "deprecated", name="code_status_enum"), default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    project = relationship("Project", back_populates="test_codes")
    requirement = relationship("Requirement", back_populates="test_codes")
    history = relationship("TestCodeHistory", back_populates="test_code", cascade="all, delete-orphan")


class TestCodeHistory(Base):
    """测试代码历史版本"""
    __tablename__ = "test_code_history"

    id = Column(String(36), primary_key=True)
    test_code_id = Column(String(36), ForeignKey("test_code.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)

    code_content = Column(Text, nullable=False)
    change_reason = Column(Text)  # 变更原因
    created_by = Column(String(36))  # 创建人ID

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    test_code = relationship("TestCode", back_populates="history")
