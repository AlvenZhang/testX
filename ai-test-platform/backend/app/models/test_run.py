from sqlalchemy import Column, String, Text, JSON, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    test_code_id = Column(String(36), ForeignKey("test_code.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum("pending", "running", "success", "failed", "cancelled", name="run_status_enum"), default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    container_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
