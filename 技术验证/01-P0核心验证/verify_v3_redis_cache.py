"""
V3验证: Redis缓存性能测试
验证方法: Redis连接、写入、读取、缓存失效
通过标准: 延迟 < 10ms

运行: python verify_v3_redis_cache.py
"""
import os
import time
import sys
import redis

# 配置 - 请修改为实际配置
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD", None),
    "decode_responses": True
}


def test_redis_cache():
    """Redis缓存性能测试"""
    print("=" * 50)
    print("V3 Redis 缓存性能测试")
    print("=" * 50)

    # 1. 连接Redis
    print("\n[1] 连接Redis...")
    try:
        client = redis.Redis(**REDIS_CONFIG)
        client.ping()
        print(f"    ok 连接成功")
        print(f"    Host: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
    except redis.ConnectionError as e:
        print(f"    fail 连接失败: {e}")
        print("    请检查Redis服务是否运行: redis-server &")
        return False

    try:
        # 2. 性能测试 - 写入
        print("\n[2] 写入性能测试 (10000次)...")

        test_data = {
            "project_id": "test-project-123",
            "config": {"framework": "pytest", "timeout": 30},
            "test_results": [f"result_{i}" for i in range(100)]
        }

        start = time.time()
        for i in range(10000):
            key = f"test:key:{i}"
            client.set(key, str(test_data))
        write_time = (time.time() - start) * 1000
        write_latency = write_time / 10000

        print(f"    总耗时: {write_time:.2f}ms")
        print(f"    平均延迟: {write_latency:.3f}ms")
        print(f"    结果: {'✓ PASS' if write_latency < 10 else '✗ FAIL'} (目标 < 10ms)")

        # 3. 性能测试 - 读取
        print("\n[3] 读取性能测试 (10000次)...")

        # 先写入
        client.set("test:read:key", str(test_data))

        start = time.time()
        for _ in range(10000):
            client.get("test:read:key")
        read_time = (time.time() - start) * 1000
        read_latency = read_time / 10000

        print(f"    总耗时: {read_time:.2f}ms")
        print(f"    平均延迟: {read_latency:.3f}ms")
        print(f"    结果: {'✓ PASS' if read_latency < 10 else '✗ FAIL'} (目标 < 10ms)")

        # 4. 批量操作测试
        print("\n[4] 批量操作测试 (MSET/MGET)...")

        batch_data = {f"batch:key:{i}": f"value:{i}" for i in range(1000)}
        start = time.time()
        client.mset(batch_data)
        mset_time = (time.time() - start) * 1000

        start = time.time()
        client.mget(list(batch_data.keys()))
        mget_time = (time.time() - start) * 1000

        print(f"    MSET (1000条): {mset_time:.2f}ms")
        print(f"    MGET (1000条): {mget_time:.2f}ms")
        print(f"    结果: {'✓ PASS' if mget_time < 50 else '✗ FAIL'} (目标 < 50ms)")

        # 5. 缓存失效测试
        print("\n[5] 缓存失效测试 (EXPIRE)...")

        client.set("test:expire:key", "value")
        client.expire("test:expire:key", 1)

        exists = client.exists("test:expire:key")
        print(f"    设置过期时间: 1秒")
        print(f"    立即检查存在: {'是' if exists else '否'}")

        time.sleep(1.1)
        exists_after = client.exists("test:expire:key")
        print(f"    1秒后检查存在: {'是' if exists_after else '否'}")
        print(f"    结果: {'✓ PASS' if not exists_after else '✗ FAIL'}")

        # 6. JSON缓存测试
        print("\n[6] JSON缓存测试...")
        import json

        json_data = {
            "projects": [
                {"id": f"proj_{i}", "name": f"Project {i}", "status": "active"}
                for i in range(100)
            ]
        }

        start = time.time()
        client.set("test:json:data", json.dumps(json_data))
        cached = json.loads(client.get("test:json:data"))
        json_time = (time.time() - start) * 1000

        print(f"    存储100个项目数据")
        print(f"    序列化/反序列化耗时: {json_time:.3f}ms")
        print(f"    数据完整性: {'✓ PASS' if len(cached['projects']) == 100 else '✗ FAIL'}")

        # 综合评估
        all_passed = (
            write_latency < 10 and
            read_latency < 10 and
            mget_time < 50 and
            not exists_after
        )

        print("\n" + "=" * 50)
        print("测试结果:")
        print(f"    写入延迟: {write_latency:.3f}ms {'✓ PASS' if write_latency < 10 else '✗ FAIL'}")
        print(f"    读取延迟: {read_latency:.3f}ms {'✓ PASS' if read_latency < 10 else '✗ FAIL'}")
        print(f"    批量读取: {mget_time:.2f}ms {'✓ PASS' if mget_time < 50 else '✗ FAIL'}")
        print(f"    过期失效: {'✓ PASS' if not exists_after else '✗ FAIL'}")
        print("=" * 50)
        print(f"V3 测试结果: {'✓ PASS' if all_passed else '✗ FAIL'}")
        print("=" * 50)

        return all_passed

    finally:
        # 清理测试数据
        print("\n[7] 清理测试数据...")
        keys_to_delete = []
        for i in range(10000):
            keys_to_delete.append(f"test:key:{i}")
        keys_to_delete.extend([
            "test:read:key", "test:expire:key", "test:json:data"
        ])
        keys_to_delete.extend([f"batch:key:{i}" for i in range(1000)])

        client.delete(*keys_to_delete)
        client.close()
        print("    ok 清理完成")


if __name__ == "__main__":
    try:
        result = test_redis_cache()
        sys.exit(0 if result else 1)
    except redis.ConnectionError as e:
        print(f"\nRedis连接错误: {e}")
        print("请确保Redis服务正在运行")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)