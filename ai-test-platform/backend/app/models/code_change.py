from sqlalchemy import Column, String, Text, JSON, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from ..core.database import Base


class CodeChange(Base):
    __tablename__ = "code_changes"

    id = Column(String(36), primary_key=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(Enum("git_commit", "git_pr", "manual", name="change_type_enum"), default="manual")
    git_url = Column(String(500))
    commit_hash = Column(String(40))
    diff_content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
