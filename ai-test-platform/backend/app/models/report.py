from sqlalchemy import Column, String, Text, JSON, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.sql import func
from ..core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True)
    test_run_id = Column(String(36), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False)
    total_cases = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    report_type = Column(Enum("new_feature", "regression", name="report_type_enum"), default="new_feature")
    report_data = Column(JSON)
    log_content = Column(Text)
    screenshots = Column(JSON)  # Array of screenshot paths
    created_at = Column(DateTime, server_default=func.now())
