"""
V1验证: FastAPI异步数据库操作性能测试
验证方法: 100并发CRUD压测
通过标准: QPS > 500

运行: python verify_v1_fastapi_performance.py
"""
import asyncio
import time
import statistics
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, text
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects_verify"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))


async def test_concurrent_crud():
    """测试100并发CRUD操作"""
    # 数据库连接配置 - 请修改为实际配置
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mysql+aiomysql://user:pass@localhost:3306/testdb"
    )

    engine = create_async_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # 创建表
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS projects_verify"))
        await conn.execute(text("""
            CREATE TABLE projects_verify (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description VARCHAR(500)
            ) ENGINE=InnoDB
        """))

    results = []

    async def create_project():
        start = time.time()
        async with async_session() as session:
            project = Project(
                id=str(uuid.uuid4()),
                name=f"test_{time.time()}",
                description="performance test"
            )
            session.add(project)
            await session.commit()
        return time.time() - start

    async def read_project():
        start = time.time()
        async with async_session() as session:
            result = await session.execute(
                text("SELECT * FROM projects_verify LIMIT 1")
            )
            result.fetchone()
        return time.time() - start

    print("=" * 50)
    print("V1 FastAPI异步性能测试")
    print("=" * 50)

    # 测试写入
    print("\n[1] 100并发写入测试")
    start_total = time.time()
    tasks = [create_project() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_total
    write_qps = 100 / total_time
    avg_write_latency = statistics.mean(results) * 1000

    print(f"    总耗时: {total_time:.2f}s")
    print(f"    QPS: {write_qps:.2f}")
    print(f"    平均延迟: {avg_write_latency:.2f}ms")

    # 测试读取
    print("\n[2] 100并发读取测试")
    start_total = time.time()
    tasks = [read_project() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_total
    read_qps = 100 / total_time
    avg_read_latency = statistics.mean(results) * 1000

    print(f"    总耗时: {total_time:.2f}s")
    print(f"    QPS: {read_qps:.2f}")
    print(f"    平均延迟: {avg_read_latency:.2f}ms")

    # 综合评估
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"    写入QPS: {write_qps:.2f} (目标 > 500) {'✓ PASS' if write_qps > 500 else '✗ FAIL'}")
    print(f"    读取QPS: {read_qps:.2f} (目标 > 500) {'✓ PASS' if read_qps > 500 else '✗ FAIL'}")
    print("=" * 50)

    # 清理
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS projects_verify"))

    await engine.dispose()

    return write_qps > 500 and read_qps > 500


if __name__ == "__main__":
    result = asyncio.run(test_concurrent_crud())
    sys.exit(0 if result else 1)
