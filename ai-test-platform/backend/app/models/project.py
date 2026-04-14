from sqlalchemy import Column, String, Text, JSON, DateTime
from sqlalchemy.sql import func

from ..core.database import Base


class Project(Base):
    """项目模型"""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    git_url = Column(String(500))
    config = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
