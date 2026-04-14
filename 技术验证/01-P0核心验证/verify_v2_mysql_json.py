"""
V2验证: MySQL JSON字段存储和查询性能测试
验证方法: 存储10万条数据，索引查询
通过标准: 查询 < 100ms

运行: python verify_v2_mysql_json.py
"""
import time
import mysql.connector
import json
import uuid
import sys

# 配置 - 请修改为实际配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "user"),
    "password": os.getenv("DB_PASS", "pass"),
    "database": os.getenv("DB_NAME", "testdb")
}

import os


def test_mysql_json():
    print("=" * 50)
    print("V2 MySQL JSON字段性能测试")
    print("=" * 50)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 1. 创建表
        print("\n[1] 创建测试表...")
        cursor.execute("DROP TABLE IF EXISTS test_json_verify")
        cursor.execute("""
            CREATE TABLE test_json_verify (
                id VARCHAR(36) PRIMARY KEY,
                config JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_created_at (created_at),
                INDEX idx_framework ((CAST(config->>'$.framework' AS CHAR(50))))
            ) ENGINE=InnoDB
        """)
        print("    创建完成")

        # 2. 批量插入10万条
        print("\n[2] 批量插入10万条数据...")
        print("    (这可能需要几分钟...)")

        batch_size = 5000
        total = 100000
        start = time.time()

        for batch_start in range(0, total, batch_size):
            data = []
            for i in range(batch_start, min(batch_start + batch_size, total)):
                config = {
                    "framework": "pytest" if i % 2 == 0 else "testng",
                    "test_types": ["functional", "api", "ui"][i % 3: (i % 3) + 2],
                    "settings": {
                        "timeout": 30 + (i % 10),
                        "retry": i % 5,
                        "parallel": i % 2 == 0
                    },
                    "metadata": {
                        "author": f"user_{i % 100}",
                        "version": f"{i % 10}.{i % 100}"
                    }
                }
                data.append((str(uuid.uuid4()), json.dumps(config)))

            cursor.executemany(
                "INSERT INTO test_json_verify (id, config) VALUES (%s, %s)",
                data
            )
            conn.commit()

            elapsed = time.time() - start
            progress = (batch_start + batch_size) / total * 100
            print(f"    进度: {progress:.1f}% ({elapsed:.1f}s)", end="\r")

        insert_time = time.time() - start
        insert_qps = total / insert_time
        print(f"\n    插入完成!")
        print(f"    总耗时: {insert_time:.2f}s")
        print(f"    插入QPS: {insert_qps:.2f}")

        # 3. JSON查询性能测试
        print("\n[3] JSON查询性能测试...")

        queries = [
            (
                "SELECT * FROM test_json_verify WHERE JSON_EXTRACT(config, '$.framework') = 'pytest' LIMIT 100",
                "JSON_EXTRACT (索引)"
            ),
            (
                "SELECT * FROM test_json_verify WHERE config->>'$.framework' = 'pytest' LIMIT 100",
                "JSON路径->> (索引)"
            ),
            (
                "SELECT * FROM test_json_verify WHERE JSON_CONTAINS(config, '\"api\"', '$.test_types') LIMIT 100",
                "JSON_CONTAINS (数组)"
            ),
            (
                "SELECT * FROM test_json_verify WHERE config->>'$.settings.timeout' > 35 LIMIT 100",
                "JSON嵌套查询"
            ),
        ]

        all_passed = True
        for sql, name in queries:
            query_start = time.time()
            cursor.execute(sql)
            results = cursor.fetchall()
            query_time = (time.time() - query_start) * 1000

            passed = query_time < 100
            if not passed:
                all_passed = False

            print(f"\n    {name}:")
            print(f"      查询时间: {query_time:.2f}ms (目标 < 100ms)")
            print(f"      返回条数: {len(results)}")
            print(f"      结果: {'✓ PASS' if passed else '✗ FAIL'}")

        # 4. 统计分析
        print("\n[4] JSON函数性能对比...")

        # Count查询
        for func in ["COUNT(*)", "COUNT(1)"]:
            start = time.time()
            cursor.execute(f"SELECT {func} FROM test_json_verify")
            cursor.fetchone()
            elapsed = (time.time() - start) * 1000
            print(f"    {func}: {elapsed:.2f}ms")

        print("\n" + "=" * 50)
        print(f"测试结果: {'✓ PASS' if all_passed else '✗ FAIL'}")
        print("=" * 50)

        return all_passed

    finally:
        cursor.execute("DROP TABLE IF EXISTS test_json_verify")
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        result = test_mysql_json()
        sys.exit(0 if result else 1)
    except mysql.connector.Error as e:
        print(f"\n数据库错误: {e}")
        print("请检查数据库配置是否正确")
        sys.exit(1)
