#!/usr/bin/env python3
"""测试数据生成脚本"""
import asyncio
import sys
import os
import uuid
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session
from app.models.user import User
from app.models.project import Project
from app.models.requirement import Requirement
from app.core.security import get_password_hash


async def create_test_users():
    """创建测试用户"""
    users = [
        {
            "id": str(uuid.uuid4()),
            "email": "admin@example.com",
            "name": "Admin User",
            "hashed_password": get_password_hash("admin123"),
        },
        {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": get_password_hash("test123"),
        },
    ]

    async with async_session() as session:
        for user_data in users:
            user = User(**user_data)
            session.add(user)
        await session.commit()

    print(f"Created {len(users)} test users")
    return users


async def create_test_projects():
    """创建测试项目"""
    projects = [
        {
            "id": str(uuid.uuid4()),
            "name": "电商平台测试",
            "description": "某电商平台的 Web/API 自动化测试项目",
            "git_url": "https://github.com/example/ecommerce-api",
            "config": {
                "test_types": ["web", "api"],
                "default_framework": "pytest",
            },
        },
        {
            "id": str(uuid.uuid4()),
            "name": "移动端测试",
            "description": "Android/iOS 移动应用测试项目",
            "git_url": "https://github.com/example/mobile-app",
            "config": {
                "test_types": ["mobile"],
                "default_framework": "appium",
            },
        },
    ]

    async with async_session() as session:
        for proj_data in projects:
            project = Project(**proj_data)
            session.add(project)
        await session.commit()

    print(f"Created {len(projects)} test projects")
    return projects


async def create_test_requirements(project_ids: list[str]):
    """创建测试需求"""
    requirements = []

    for project_id in project_ids:
        reqs = [
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "title": "用户登录功能",
                "description": "支持邮箱密码登录，支持记住登录状态",
                "priority": "high",
                "status": "pending",
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "title": "商品搜索功能",
                "description": "支持关键词搜索，支持分类筛选",
                "priority": "medium",
                "status": "pending",
            },
            {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "title": "购物车功能",
                "description": "支持添加商品、修改数量、删除商品",
                "priority": "high",
                "status": "pending",
            },
        ]
        requirements.extend(reqs)

    async with async_session() as session:
        for req_data in requirements:
            req = Requirement(**req_data)
            session.add(req)
        await session.commit()

    print(f"Created {len(requirements)} test requirements")
    return requirements


async def main():
    """主函数"""
    print("=" * 50)
    print("Test Data Seeding Script")
    print("=" * 50)

    try:
        users = await create_test_users()
        projects = await create_test_projects()
        await create_test_requirements([p["id"] for p in projects])

        print("\nTest data seeding completed!")
        print("\nTest accounts:")
        print("  - admin@example.com / admin123")
        print("  - test@example.com / test123")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
