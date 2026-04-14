"""需求版本历史模型"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class RequirementVersion(Base):
    """需求版本历史"""
    __tablename__ = "requirement_versions"

    id = Column(String(36), primary_key=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)

    title = Column(String(500))
    description = Column(Text)
    priority = Column(String(20))  # low/medium/high/critical
    status = Column(String(50))

    diff = Column(JSON)  # 变更内容对比
    created_by = Column(String(36))  # 创建人ID
    change_reason = Column(Text)  # 变更原因

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    requirement = relationship("Requirement", back_populates="versions")
