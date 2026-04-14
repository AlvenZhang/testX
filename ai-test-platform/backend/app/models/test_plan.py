from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base


class TestPlan(Base):
    __tablename__ = "test_plans"

    id = Column(String(36), primary_key=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    test_scope = Column(Text)
    test_types = Column(JSON)  # Array of test types
    test_strategy = Column(Text)
    risk_points = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
