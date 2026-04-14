from sqlalchemy import Column, String, Text, JSON, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.sql import func
from ..core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(String(50), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    steps = Column(Text)  # JSON array format
    expected_result = Column(Text)
    priority = Column(Enum("low", "medium", "high", name="case_priority_enum"), default="medium")
    status = Column(Enum("active", "deprecated", name="case_status_enum"), default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
