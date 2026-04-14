#!/usr/bin/env python3
"""数据库初始化脚本"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine, async_session
from app.core.config import get_settings


async def init_database():
    """初始化数据库表"""
    settings = get_settings()
    print(f"Initializing database: {settings.database_url}")

    async with engine.begin() as conn:
        # 创建所有表
        # 注意: 实际生产环境应该使用 Alembic 进行迁移
        # 这里只是演示如何创建表

        # 检查数据库连接
        await conn.execute(text("SELECT 1"))

    print("Database connection successful!")

    # 创建表（如果有 models 的话）
    # from app.models.base import Base
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    print("Database initialization completed!")


async def create_indexes():
    """创建索引"""
    indexes = [
        # Projects indexes
        "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)",

        # Requirements indexes
        "CREATE INDEX IF NOT EXISTS idx_requirements_project_id ON requirements(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_requirements_status ON requirements(status)",

        # Test Cases indexes
        "CREATE INDEX IF NOT EXISTS idx_test_cases_requirement_id ON test_cases(requirement_id)",

        # Test Runs indexes
        "CREATE INDEX IF NOT EXISTS idx_test_runs_project_id ON test_runs(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs(status)",

        # Reports indexes
        "CREATE INDEX IF NOT EXISTS idx_reports_test_run_id ON reports(test_run_id)",
    ]

    async with async_session() as session:
        for idx_sql in indexes:
            try:
                await session.execute(text(idx_sql))
                print(f"Created index: {idx_sql[:50]}...")
            except Exception as e:
                print(f"Index creation skipped (may already exist): {e}")
        await session.commit()


async def main():
    """主函数"""
    print("=" * 50)
    print("Database Initialization Script")
    print("=" * 50)

    try:
        await init_database()
        # await create_indexes()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
