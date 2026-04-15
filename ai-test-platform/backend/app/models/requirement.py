from sqlalchemy import Column, String, Text, JSON, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    priority = Column(Enum("low", "medium", "high", "critical", name="priority_enum"), default="medium")
    status = Column(Enum("pending", "cases_generated", "code_generated", "tested", name="status_enum"), default="pending")
    version = Column(Integer, default=1)
    extra = Column("metadata", JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    test_cases = relationship("TestCase", back_populates="requirement")


class RequirementVersion(Base):
    __tablename__ = "requirement_versions"

    id = Column(String(36), primary_key=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    diff = Column(JSON)
    created_by = Column(String(36))
    created_at = Column(DateTime, server_default=func.now())
