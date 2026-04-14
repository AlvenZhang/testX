"""测试代码历史模型"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


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
