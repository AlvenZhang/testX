# AI自动化测试平台 - 技术验证执行方案

## 验证目标

在 **5个工作日** 内完成 **P0核心风险验证**，验证失败则立即启动备选方案，不阻塞项目。

## 验证环境准备清单

### 硬件要求

| 设备 | 数量 | 要求 | 用途 |
|------|------|------|------|
| 开发服务器 | 1台 | Linux (Ubuntu 20.04+), 4核8G | Backend + Docker |
| Android真机 | 1台 | Android 10+, 已开启USB调试 | Appium测试 |
| Mac电脑(iOS) | 1台 | macOS + Xcode | iOS测试(可选) |

### 软件环境

```bash
# 服务器端
- Docker 20.10+
- MySQL 8.0
- Redis 6.0+
- Python 3.11+
- Node.js 18+

# Android端
- USB调试已开启
- adb工具
- Appium Server 2.x

# iOS端(可选)
- macOS
- Xcode
- Appium Server 2.x
- WebDriverAgent
```

---

## Day 1-2: P0核心风险验证

### V1: FastAPI异步性能验证

**验证目标**: QPS > 500

**实现代码** `verify_v1_fastapi_performance.py`:
```python
"""
V1验证: FastAPI异步数据库操作性能测试
验证方法: 100并发CRUD压测
通过标准: QPS > 500
"""
import asyncio
import time
import statistics
from locust import HttpUser, task, between, events
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, select
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))

# 测试脚本
async def test_concurrent_crud():
    engine = create_async_engine(
        "mysql+aiomysql://user:pass@host:3306/testdb",
        pool_size=20,
        max_overflow=30
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results = []

    async def create_project():
        start = time.time()
        async with async_session() as session:
            import uuid
            project = Project(id=str(uuid.uuid4()), name="test", description="desc")
            session.add(project)
            await session.commit()
        return time.time() - start

    # 100并发
    start_total = time.time()
    tasks = [create_project() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_total

    qps = 100 / total_time
    avg_latency = statistics.mean(results)

    print(f"=== V1 FastAPI性能测试结果 ===")
    print(f"总耗时: {total_time:.2f}s")
    print(f"QPS: {qps:.2f}")
    print(f"平均延迟: {avg_latency*1000:.2f}ms")
    print(f"PASS: {qps > 500}")

# 运行: python verify_v1_fastapi_performance.py
```

### V2: MySQL JSON字段验证

**验证目标**: 查询 < 100ms

**实现代码** `verify_v2_mysql_json.py`:
```python
"""
V2验证: MySQL JSON字段存储和查询性能测试
验证方法: 存储10万条数据，索引查询
通过标准: 查询 < 100ms
"""
import time
import mysql.connector
import json
import uuid

def test_mysql_json():
    conn = mysql.connector.connect(
        host="localhost",
        user="user",
        password="pass",
        database="testdb"
    )
    cursor = conn.cursor()

    # 1. 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_json (
            id VARCHAR(36) PRIMARY KEY,
            config JSON,
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB
    """)

    # 2. 批量插入10万条
    print("插入10万条数据...")
    start = time.time()
    data = []
    for i in range(100000):
        config = {
            "framework": "pytest",
            "test_types": ["functional", "api"],
            "settings": {"timeout": 30, "retry": 3}
        }
        data.append((str(uuid.uuid4()), json.dumps(config)))

    cursor.executemany(
        "INSERT INTO test_json (id, config) VALUES (%s, %s)",
        data
    )
    conn.commit()
    insert_time = time.time() - start
    print(f"插入耗时: {insert_time:.2f}s")

    # 3. JSON查询性能测试
    print("执行JSON查询...")
    queries = [
        # JSON字段直接查询
        ("SELECT * FROM test_json WHERE JSON_EXTRACT(config, '$.framework') = 'pytest' LIMIT 100", "JSON_EXTRACT"),
        # JSON数组包含查询
        ("SELECT * FROM test_json WHERE JSON_CONTAINS(config, '\"api\"', '$.test_types') LIMIT 100", "JSON_CONTAINS"),
    ]

    for sql, name in queries:
        start = time.time()
        cursor.execute(sql)
        results = cursor.fetchall()
        query_time = (time.time() - start) * 1000
        print(f"{name}: {query_time:.2f}ms, 返回{len(results)}条")
        print(f"  PASS: {query_time < 100}")

    cursor.close()
    conn.close()

# 运行: python verify_v2_mysql_json.py
```

### V5: Android真机ADB连接验证

**验证目标**: adb网络连接成功，截图成功

**实现代码** `verify_v5_android_adb.py`:
```python
"""
V5验证: Android真机网络连接
验证方法: adb connect + screencap
通过标准: 截图成功

前置条件:
1. Android手机开启USB调试
2. 手机和服务器在同一网络
3. 手机开启网络ADB: adb tcpip 5555
"""
import subprocess
import time

def test_android_adb_connection():
    device_ip = "192.168.1.100"  # TODO: 修改为实际IP
    device_port = 5555

    print(f"=== V5 Android ADB连接测试 ===")
    print(f"目标设备: {device_ip}:{device_port}")

    # 1. 连接设备
    print("1. 执行 adb connect...")
    result = subprocess.run(
        ["adb", "connect", f"{device_ip}:{device_port}"],
        capture_output=True, text=True
    )
    print(f"   输出: {result.stdout}")
    if "connected" not in result.stdout and "already connected" not in result.stdout:
        print("   FAIL: 连接失败")
        return False

    # 2. 检查设备状态
    print("2. 检查设备状态...")
    result = subprocess.run(
        ["adb", "-s", f"{device_ip}:{device_port}", "get-state"],
        capture_output=True, text=True
    )
    print(f"   状态: {result.stdout.strip()}")

    # 3. 截图
    print("3. 执行截图...")
    result = subprocess.run(
        ["adb", "-s", f"{device_ip}:{device_port}", "exec-out", "screencap", "-p"],
        capture_output=True
    )

    if len(result.stdout) > 1000:
        # 保存截图
        with open("/tmp/verify_screenshot.png", "wb") as f:
            f.write(result.stdout)
        print(f"   PASS: 截图成功, 大小: {len(result.stdout)} bytes")
        return True
    else:
        print(f"   FAIL: 截图失败或图片过小")
        return False

# 运行: python verify_v5_android_adb.py
```

### V6: Appium Android验证

**验证目标**: 执行简单测试用例，截图成功

**实现代码** `verify_v6_appium_android.py`:
```python
"""
V6验证: Appium Android自动化测试
验证方法: 启动Appium，连接设备，执行简单测试
通过标准: 测试通过，截图成功

前置条件:
1. Appium Server 2.x 已安装并启动
2. V5验证已通过(adb连接正常)
3. Android设备已连接
"""
import time
from appium import webdriver
from appium.webdriver.extensions.android.nativekey import AndroidKey

def test_appium_android():
    device_ip = "192.168.1.100"
    appium_port = 4723

    desired_caps = {
        "platformName": "Android",
        "deviceName": "TestDevice",
        "udid": f"{device_ip}:5555",
        "automationName": "UiAutomator2",
        "noReset": True,
        "newCommandTimeout": 300,
        "skipUnlock": True,
    }

    print(f"=== V6 Appium Android测试 ===")
    print(f"Appium地址: http://localhost:{appium_port}")

    # 1. 连接Appium
    print("1. 连接Appium...")
    driver = webdriver.Remote(
        f"http://localhost:{appium_port}/wd/hub",
        desired_caps
    )

    try:
        # 2. 启动设置应用
        print("2. 启动设置应用...")
        driver.start_activity("com.android.settings", ".Settings")
        time.sleep(2)

        # 3. 获取页面源码
        print("3. 获取页面源码...")
        source = driver.page_source
        print(f"   页面大小: {len(source)} chars")

        # 4. 截图
        print("4. 执行截图...")
        screenshot = driver.save_screenshot("/tmp/verify_appium_screenshot.png")
        print(f"   截图路径: /tmp/verify_appium_screenshot.png")

        # 5. 简单交互测试
        print("5. 简单交互测试...")
        # 点击搜索按钮(如果存在)
        try:
            search_btn = driver.find_element_by_accessibility_id("Search")
            search_btn.click()
            print("   点击搜索按钮成功")
        except:
            print("   跳过搜索按钮(未找到)")

        print("=== V6 PASS: Appium Android测试成功 ===")
        return True

    except Exception as e:
        print(f"=== V6 FAIL: {str(e)} ===")
        return False

    finally:
        driver.quit()

# 运行: python verify_v6_appium_android.py
```

### V7: Appium iOS验证(可选)

**验证目标**: 执行简单测试用例，截图成功

**实现代码** `verify_v7_appium_ios.py`:
```python
"""
V7验证: Appium iOS自动化测试
验证方法: 启动WDA，执行简单测试
通过标准: 测试通过，截图成功

前置条件:
1. macOS机器
2. Xcode已安装
3. iOS设备或模拟器
4. Appium Server已安装

注意: 此测试必须在macOS上运行
"""
import time
from appium import webdriver

def test_appium_ios():
    desired_caps = {
        "platformName": "iOS",
        "deviceName": "iPhone 15 Pro",
        "platformVersion": "17.0",
        "automationName": "XCUITest",
        "bundleId": "com.apple.mobilesettings",
        "useNewWDA": True,
        "noReset": True,
    }

    print(f"=== V7 Appium iOS测试 ===")

    driver = webdriver.Remote(
        "http://localhost:4723/wd/hub",
        desired_caps
    )

    try:
        # 获取页面源码
        source = driver.page_source
        print(f"页面大小: {len(source)} chars")

        # 截图
        screenshot = driver.save_screenshot("/tmp/verify_ios_screenshot.png")
        print(f"截图成功")

        print("=== V7 PASS ===")
        return True

    except Exception as e:
        print(f"=== V7 FAIL: {str(e)} ===")
        return False

    finally:
        driver.quit()

# 运行(仅macOS): python verify_v7_appium_ios.py
```

---

## Day 3-4: P1重要功能验证

### V3: Redis缓存验证

**实现代码** `verify_v3_redis_cache.py`:
```python
"""V3验证: Redis缓存测试"""
import redis
import time
import hashlib

def test_redis_cache():
    r = redis.Redis(host='localhost', port=6379, db=0)

    test_data = {"requirement": "用户登录功能", "code": "login.py"}

    # 生成cache key
    cache_key = f"ai:cache:{hashlib.md5(str(test_data).encode()).hexdigest()}"

    print("=== V3 Redis缓存测试 ===")

    # 第一次查询(未命中)
    print("1. 第一次查询...")
    cached = r.get(cache_key)
    print(f"   缓存命中: {cached is not None}")

    # 写入缓存
    print("2. 写入缓存...")
    r.setex(cache_key, 3600, str(test_data))  # 1小时过期

    # 第二次查询(应该命中)
    print("3. 第二次查询...")
    cached = r.get(cache_key)
    print(f"   缓存命中: {cached is not None}")
    print(f"   PASS: {cached is not None}")

    # 清理
    r.delete(cache_key)
```

### V4: Docker沙箱Web测试验证

**Dockerfile.sandbox**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
RUN pip install pytest pytest-html playwright requests

# 安装浏览器(用于Web测试)
RUN playwright install --with-deps chromium

# 复制执行脚本
COPY executor/ /app/executor/

CMD ["python", "/app/executor/run_web_test.py"]
```

**验证脚本** `verify_v4_docker_sandbox.py`:
```python
"""V4验证: Docker沙箱Web测试执行"""
import docker
import time
import subprocess

def test_docker_sandbox():
    client = docker.from_env()
    image_name = "web-test-sandbox"

    print("=== V4 Docker沙箱测试 ===")

    # 1. 构建镜像
    print("1. 构建镜像...")
    start = time.time()
    client.images.build(path="./sandbox/", tag=image_name)
    build_time = time.time() - start
    print(f"   构建耗时: {build_time:.2f}s")

    # 2. 运行测试容器
    print("2. 启动容器...")
    container = client.containers.run(
        image_name,
        detach=True,
        mem_limit="1g",
        network_mode="bridge"
    )

    # 3. 等待执行完成
    print("3. 等待测试完成...")
    result = container.wait()
    logs = container.logs().decode()

    # 4. 清理
    container.remove()

    total_time = time.time() - start
    print(f"总耗时: {total_time:.2f}s")
    print(f"PASS: {total_time < 30 and result['StatusCode'] == 0}")
```

### V8-V11: AI能力验证

详见 `verify_ai/` 目录

---

## Day 5: P2 + 总结

### 验证结果记录模板

```markdown
# 技术验证报告 - YYYY-MM-DD

## P0核心风险验证结果

| 验证项 | 结果 | 备注 |
|--------|------|------|
| V1 FastAPI性能 | PASS/FAIL | QPS: XXX |
| V2 MySQL JSON | PASS/FAIL | 查询: XXXms |
| V5 Android ADB | PASS/FAIL | 连接: XXX |
| V6 Appium Android | PASS/FAIL | 测试: XXX |
| V7 Appium iOS | PASS/FAIL/SKIP | - |

## P1重要功能验证结果

| 验证项 | 结果 | 备注 |
|--------|------|------|
| V3 Redis缓存 | PASS/FAIL | - |
| V4 Docker沙箱 | PASS/FAIL | - |
| V8 AI用例生成 | PASS/FAIL | 质量: XX% |
| V9 AI影响分析 | PASS/FAIL | 召回: XX% |
| V10 AI代码修复 | PASS/FAIL | 可运行: XX% |
| V11 AI稳定性 | PASS/FAIL | 成功率: XX% |

## 风险登记册

| 风险 | 影响 | 应对策略 | 责任人 |
|------|------|---------|--------|
| XXX | 高/中/低 | XXX | XXX |

## 结论

- [ ] P0全部通过，可以进入阶段一开发
- [ ] 存在P0失败，需要启动备选方案
```
