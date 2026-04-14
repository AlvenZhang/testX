# AI自动化测试平台 - 技术实现方案

## Context

用户需要一个「多项目AI驱动自动化测试平台」，实现从"需求+代码变更"到"测试执行+回归测试"的全流程自动化。核心痛点：多项目并行管理、需求变更导致旧测试代码失效、回归测试成本高。

**已确认的技术选择：**
- AI模型：支持多模型切换（GPT-4o/DeepSeek/通义千问）
- 测试执行引擎：Docker沙箱隔离
- 数据库：MySQL
- **客户端测试**：Android (Appium) + iOS (Appium/XCTest)

其他技术栈：React18+TypeScript（前端）、FastAPI+Python3.11+（后端）、Redis（缓存）、Docker（部署）。

---

## 一、项目目录结构

```
ai-test-platform/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/                      # API路由层
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── projects.py       # 项目管理接口
│   │   │   │   ├── requirements.py   # 需求管理接口
│   │   │   │   ├── test_cases.py     # 测试用例接口
│   │   │   │   ├── test_code.py      # 测试代码接口
│   │   │   │   ├── test_runs.py      # 测试执行接口
│   │   │   │   ├── reports.py        # 报告接口
│   │   │   │   ├── devices.py        # 设备管理接口
│   │   │   │   └── ai_analysis.py    # AI分析接口
│   │   │   └── deps.py               # 依赖注入（获取用户、校验权限）
│   │   ├── core/                     # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # 配置管理（环境变量、模型配置）
│   │   │   ├── security.py           # JWT认证、权限校验
│   │   │   └── database.py           # 数据库连接池
│   │   ├── models/                   # SQLAlchemy模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # 基础模型类
│   │   │   ├── project.py            # 项目模型
│   │   │   ├── requirement.py         # 需求模型
│   │   │   ├── test_case.py          # 测试用例模型
│   │   │   ├── test_code.py          # 测试代码模型
│   │   │   ├── test_run.py           # 测试执行记录模型
│   │   │   ├── report.py             # 测试报告模型
│   │   │   ├── device.py             # 设备模型（Android/iOS真机/模拟器）
│   │   │   └── user.py               # 用户模型
│   │   ├── schemas/                  # Pydantic请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── requirement.py
│   │   │   ├── test_case.py
│   │   │   ├── test_code.py
│   │   │   ├── test_run.py
│   │   │   ├── report.py
│   │   │   ├── device.py
│   │   │   └── common.py              # 通用响应、分页模型
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py    # 项目CRUD、成员管理
│   │   │   ├── requirement_service.py # 需求CRUD、版本管理
│   │   │   ├── ai_service.py         # AI大模型调用（多模型切换）
│   │   │   ├── git_service.py         # Git操作（克隆、diff解析）
│   │   │   ├── code_gen_service.py    # 测试代码生成
│   │   │   ├── code_fix_service.py    # 测试代码修复
│   │   │   ├── test_executor.py       # 测试执行引擎
│   │   │   ├── mobile_executor.py     # 移动端测试执行（Appium）
│   │   │   ├── device_service.py      # 设备管理（连接真机/模拟器）
│   │   │   ├── report_service.py      # 报告生成
│   │   │   └── impact_service.py      # AI影响分析
│   │   ├── utils/                    # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── markdown.py            # Markdown解析
│   │   │   ├── file_utils.py          # 文件处理
│   │   │   ├── json_utils.py          # JSON序列化
│   │   │   └── screenshot_utils.py    # 截图处理
│   │   ├── workers/                  # 异步任务
│   │   │   ├── __init__.py
│   │   │   ├── test_task.py          # 测试执行任务
│   │   │   └── ai_task.py            # AI任务
│   │   └── main.py                   # FastAPI入口
│   ├── tests/                        # 后端测试
│   │   ├── __init__.py
│   │   ├── api/                      # API测试
│   │   ├── services/                 # 服务单元测试
│   │   └── conftest.py               # pytest配置
│   ├── scripts/                      # 脚本
│   │   ├── init_db.py               # 数据库初始化
│   │   └── seed_data.py              # 测试数据
│   ├── Dockerfile
│   ├── Dockerfile.sandbox            # 沙箱镜像
│   └── requirements.txt
│
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── api/                      # API请求封装
│   │   │   ├── client.ts             # axios实例
│   │   │   ├── projects.ts
│   │   │   ├── requirements.ts
│   │   │   ├── testCases.ts
│   │   │   ├── testCode.ts
│   │   │   ├── testRuns.ts
│   │   │   ├── reports.ts
│   │   │   └── ai.ts
│   │   ├── components/               # 通用组件
│   │   │   ├── CodeEditor/            # Monaco编辑器封装
│   │   │   │   ├── index.tsx
│   │   │   │   └── useEditor.ts
│   │   │   ├── DiffViewer/            # 代码对比组件
│   │   │   │   ├── index.tsx
│   │   │   │   └── DiffView.tsx
│   │   │   ├── Charts/                # 报告图表
│   │   │   │   ├── PassRatePie.tsx
│   │   │   │   └── TrendLine.tsx
│   │   │   ├── DeviceSelector/        # 设备选择器
│   │   │   │   └── index.tsx
│   │   │   ├── RequirementForm/       # 需求表单
│   │   │   │   └── index.tsx
│   │   │   ├── TestCaseTable/         # 用例表格
│   │   │   │   └── index.tsx
│   │   │   └── ExecutionLog/          # 执行日志
│   │   │       └── index.tsx
│   │   ├── pages/                    # 页面
│   │   │   ├── Projects/
│   │   │   │   ├── index.tsx         # 项目列表页
│   │   │   │   ├── [id].tsx           # 项目详情页
│   │   │   │   └── components/        # 项目相关组件
│   │   │   ├── Requirements/
│   │   │   │   ├── index.tsx         # 需求列表页
│   │   │   │   ├── [id].tsx          # 需求详情页
│   │   │   │   └── ImpactAnalysis.tsx # 影响分析组件
│   │   │   ├── TestCases/
│   │   │   │   ├── index.tsx         # 用例列表页
│   │   │   │   └── [id].tsx          # 用例编辑页
│   │   │   ├── TestCode/
│   │   │   │   ├── index.tsx         # 代码列表页
│   │   │   │   └── [id].tsx          # 代码编辑页
│   │   │   ├── TestExecution/
│   │   │   │   ├── index.tsx         # 执行列表页
│   │   │   │   ├── [id].tsx          # 执行详情页
│   │   │   │   └── DevicePool.tsx    # 设备池管理
│   │   │   ├── Reports/
│   │   │   │   ├── index.tsx         # 报告列表页
│   │   │   │   └── [id].tsx          # 报告详情页
│   │   │   └── Dashboard/
│   │   │       └── index.tsx         # 仪表盘
│   │   ├── layouts/
│   │   │   ├── BasicLayout.tsx       # 基础布局
│   │   │   ├── BlankLayout.tsx       # 空白布局
│   │   │   └── components/
│   │   │       ├── Header.tsx
│   │   │       ├── Sider.tsx
│   │   │       └── Menu.tsx
│   │   ├── store/                    # 状态管理(Zustand)
│   │   │   ├── userStore.ts
│   │   │   ├── projectStore.ts
│   │   │   └── executionStore.ts
│   │   ├── hooks/                    # 自定义Hooks
│   │   │   ├── useAsyncRun.ts        # 异步执行Hook
│   │   │   ├── useWebSocket.ts       # WebSocket Hook
│   │   │   └── usePermission.ts      # 权限 Hook
│   │   ├── services/                 # 业务服务
│   │   │   ├── aiService.ts          # AI服务封装
│   │   │   └── exportService.ts      # 导出服务
│   │   ├── types/                    # TypeScript类型
│   │   │   ├── api.d.ts
│   │   │   ├── project.d.ts
│   │   │   └── test.d.ts
│   │   ├── utils/                    # 工具函数
│   │   │   ├── formatters.ts
│   │   │   └── validators.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   │   └── screenshots/              # 截图存储目录
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
│
├── sandbox/                          # 测试执行沙箱
│   ├── docker/
│   │   ├── Dockerfile                # 测试环境镜像
│   │   └── entrypoint.sh
│   ├── executor/                    # 执行器脚本
│   │   ├── __init__.py
│   │   ├── run_api_test.py          # 接口测试执行器
│   │   ├── run_web_test.py          # Web UI测试执行器
│   │   ├── run_mobile_test.py       # 移动端测试执行器
│   │   ├── run_unit_test.py         # 单元测试执行器
│   │   └── utils.py                 # 执行器工具函数
│   └── device_controller.py         # 设备控制器（管理真机/模拟器连接）
│
├── android-device-farm/             # Android设备管理
│   ├── adb_utils.py                # ADB工具封装
│   ├── appium_server.py             # Appium服务器管理
│   └── device_pool.py               # 设备池管理
│
├── ios-device-farm/                 # iOS设备管理
│   ├── xcrun_utils.py               # XCRun工具封装
│   ├── appium_server.py             # Appium服务器管理(iOS)
│   ├── xcrunner.py                  # XCUITest执行器
│   └── device_pool.py               # 设备池管理
│
├── docker-compose.yml                # 容器编排
├── init.sql                          # 数据库初始化脚本
└── README.md
```

---

## 二、文件实现思路详解

### 2.1 后端核心文件实现

#### `backend/app/main.py` - FastAPI入口
```python
# 实现思路：
# 1. 创建FastAPI实例，注册中间件（CORS、Session）
# 2. 注册API路由（/api/v1/*）
# 3. 初始化数据库连接（startup事件）
# 4. 配置WebSocket端点用于实时日志推送
# 5. 配置异常处理器
# 6. 挂载静态文件（截图、报告）

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化数据库连接池、连接设备控制服务
    await init_db()
    await device_farm.init()
    yield
    # 关闭时：释放资源
    await close_db()
    await device_farm.cleanup()

app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
```

#### `backend/app/core/config.py` - 配置管理
```python
# 实现思路：
# 1. 使用pydantic_settings管理环境变量
# 2. AI模型配置：支持多模型切换，通过MODEL_NAME指定
# 3. 数据库配置：MySQL连接信息
# 4. Redis配置：缓存和WebSocket状态存储
# 5. 沙箱配置：Docker容器池大小、超时时间

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AI模型配置
    AI_MODEL_NAME: str = "deepseek-v2"  # 可选: gpt-4o, deepseek-v2, qwen
    OPENAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    ALIYUN_API_KEY: str = ""

    # 数据库
    DATABASE_URL: str = "mysql+pymysql://user:pass@localhost:3306/aitest"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # 沙箱配置
    SANDBOX_POOL_SIZE: int = 5
    SANDBOX_TIMEOUT: int = 3600  # 秒

    class Config:
        env_file = ".env"
```

#### `backend/app/core/security.py` - JWT认证
```python
# 实现思路：
# 1. JWT Token生成和验证
# 2. 密码哈希（bcrypt）
# 3. 依赖注入：获取当前用户
# 4. 项目权限校验函数

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

async def get_current_user(token: str) -> User:
    # 验证token并返回用户
    ...

async def check_project_permission(
    project_id: str,
    user_id: str,
    required_role: str  # viewer, editor, executor, admin
) -> bool:
    # 查询project_members表校验权限
    ...
```

#### `backend/app/models/base.py` - 基础模型
```python
# 实现思路：
# 1. SQLAlchemy Base定义
# 2. 所有模型继承Base
# 3. UUID主键生成策略
# 4. 时间戳自动更新

from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### `backend/app/models/project.py` - 项目模型
```python
# 实现思路：
# 1. 项目表：id, name, description, git_url, config(JSON测试框架配置)
# 2. config字段存储：测试类型(web/android/ios)、默认框架、API地址等
# 3. 关系：一对多（需求、用例、代码、执行记录）

class Project(BaseModel):
    __tablename__ = "projects"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    git_url = Column(String(500))
    config = Column(JSON)  # {"test_types": ["web", "android", "ios"], "default_framework": "pytest"}

    # 关系
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    test_codes = relationship("TestCode", back_populates="project")
    test_runs = relationship("TestRun", back_populates="project")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(BaseModel):
    __tablename__ = "project_members"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    user_id = Column(String(36), ForeignKey("users.id"))
    role = Column(Enum("viewer", "editor", "executor", "admin"))

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_members")
```

#### `backend/app/models/device.py` - 设备模型（新增）
```python
# 实现思路：
# 1. 设备表：管理Android/iOS真机和模拟器
# 2. 设备状态：online, offline, busy, maintaining
# 3. 连接信息：adb_serialno(Android), uuid(iOS), appium端口等

class Device(BaseModel):
    __tablename__ = "devices"

    name = Column(String(100), nullable=False)  # 设备名称
    platform = Column(Enum("android", "ios"), nullable=False)
    device_type = Column(Enum("real_device", "emulator", "simulator"), nullable=False)

    # 连接信息
    serial = Column(String(100))  # ADB serialno / iOS uuid
    appium_port = Column(Integer)
    wda_port = Column(Integer)  # iOS WebDriverAgent端口

    # 状态管理
    status = Column(Enum("online", "offline", "busy", "maintaining"), default="offline")
    current_run_id = Column(String(36), ForeignKey("test_runs.id"), nullable=True)

    # 设备信息
    os_version = Column(String(20))  # Android 13 / iOS 17
    manufacturer = Column(String(50))  # Samsung, Apple
    model = Column(String(50))  # Galaxy S24, iPhone 15 Pro

    # 能力配置
    capabilities = Column(JSON)  # {"noReset": true, "automationName": "UiAutomator2"}
```

#### `backend/app/services/ai_service.py` - AI服务
```python
# 实现思路：
# 1. 多模型适配器模式：每个模型一个适配器类
# 2. 模型工厂：根据配置创建对应的适配器
# 3. 重试机制：3次重试，指数退避
# 4. 结果缓存：Redis缓存相同输入的AI响应
# 5. 超时控制：30秒超时

import httpx
from abc import ABC, abstractmethod
from typing import dict, Any
import json

class AIModelAdapter(ABC):
    @abstractmethod
    async def chat(self, messages: list, **kwargs) -> str:
        pass

class DeepSeekAdapter(AIModelAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.deepseek.com/chat/completions"

    async def chat(self, messages: list, **kwargs) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": "deepseek-chat", "messages": messages}
            )
            return response.json()["choices"][0]["message"]["content"]

class GPTAdapter(AIModelAdapter):
    # 类似实现，使用OpenAI API

class QwenAdapter(AIModelAdapter):
    # 类似实现，使用阿里云API

class AIService:
    # 模型配置映射
    MODEL_CONFIGS = {
        "gpt-4o": {"adapter": GPTAdapter, "model": "gpt-4o"},
        "deepseek-v2": {"adapter": DeepSeekAdapter, "model": "deepseek-chat"},
        "qwen": {"adapter": QwenAdapter, "model": "qwen-turbo"}
    }

    def __init__(self, model_name: str = "deepseek-v2"):
        config = self.MODEL_CONFIGS[model_name]
        self.adapter = config["adapter"](self._get_api_key(model_name))

    async def analyze_requirement(self, requirement: str, code_diff: str) -> dict:
        """分析需求，生成测试方案与用例"""
        prompt = f"""
        你是专业的测试工程师。根据以下需求和代码变更，生成测试方案和用例。

        需求：
        {requirement}

        代码变更：
        {code_diff}

        请以JSON格式输出：
        {{
            "test_plan": {{
                "scope": "测试范围",
                "types": ["功能测试", "边界测试"],
                "strategy": "测试策略",
                "risk_points": ["风险点"]
            }},
            "test_cases": [
                {{
                    "case_id": "TC001",
                    "title": "用例标题",
                    "steps": ["步骤1", "步骤2"],
                    "expected_result": "预期结果",
                    "priority": "high"
                }}
            ]
        }}
        """
        result = await self.adapter.chat([{"role": "user", "content": prompt}])
        return json.loads(result)

    async def analyze_impact(self, new_req: str, old_reqs: list, old_codes: list, changes: str) -> dict:
        """AI影响分析"""
        prompt = f"""
        分析新需求对现有测试的影响。

        新需求：{new_req}
        现有需求：{json.dumps(old_reqs, ensure_ascii=False)}
        现有测试代码：{json.dumps(old_codes, ensure_ascii=False)}
        代码变更：{changes}

        输出JSON格式的影响分析报告。
        """
        ...

    async def fix_test_code(self, code: str, requirement: str, changes: str) -> dict:
        """修复失效的测试代码"""
        prompt = f"""
        修复以下测试代码，使其适配新的需求和代码变更。

        原测试代码：
        {code}

        新需求：
        {requirement}

        代码变更：
        {changes}

        输出JSON：
        {{
            "fixed_code": "修复后的代码",
            "changes": ["修改点1", "修改点2"],
            "reason": "修改原因"
        }}
        """
        ...

    async def generate_mobile_test_code(self, test_cases: list, platform: str) -> str:
        """生成移动端测试代码（Android Appium / iOS XCUITest）"""
        if platform == "android":
            return await self._generate_appium_python(test_cases)
        else:
            return await self._generate_xcuitest_swift(test_cases)
```

#### `backend/app/services/test_executor.py` - 测试执行引擎
```python
# 实现思路：
# 1. 任务队列：使用Redis队列管理待执行的测试任务
# 2.  Worker进程：多个worker从队列取任务执行
# 3.  Docker沙箱：为每个任务创建独立的Docker容器
# 4.  执行流程：创建容器 → 复制代码 → 安装依赖 → 执行 → 捕获结果 → 销毁容器
# 5.  实时日志：通过Redis Pub/Sub推送到WebSocket

import docker
import subprocess
import redis
import uuid
from pathlib import Path

class TestExecutor:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.redis_client = redis.Redis.from_url(REDIS_URL)
        self.sandbox_image = "ai-test-sandbox:latest"

    async def execute_test(self, run_id: str, code_path: str, test_type: str) -> dict:
        """执行测试"""
        container = None
        try:
            # 1. 创建沙箱容器
            container = await self._create_sandbox(run_id)

            # 2. 复制测试代码到容器
            await self._copy_code(container, code_path)

            # 3. 安装依赖
            await self._install_dependencies(container, test_type)

            # 4. 执行测试
            result = await self._run_tests(container, test_type)

            # 5. 捕获日志和截图
            logs = await self._get_logs(container)
            screenshots = await self._get_screenshots(container)

            return {
                "status": "success",
                "logs": logs,
                "screenshots": screenshots,
                "result": result
            }
        finally:
            if container:
                await self._destroy_sandbox(container)

    async def _create_sandbox(self, run_id: str) -> str:
        """创建Docker沙箱容器"""
        container = self.docker_client.containers.run(
            self.sandbox_image,
            detach=True,
            mem_limit="2g",
            cpu_period=100000,
            cpu_quota=200000,  # 2 CPU cores
            network_mode="bridge",
            hostname=f"test-run-{run_id}"
        )
        return container.id
```

#### `backend/app/services/mobile_executor.py` - 移动端测试执行（新增）
```python
# 实现思路：
# 1. 设备管理：连接Android/iOS设备（真机/模拟器）
# 2. Appium服务器：为每台设备启动Appium服务器
# 3. 测试执行：通过Appium执行移动端自动化测试
# 4. 截图捕获：实时获取测试截图
# 5. 设备池：管理设备分配和回收

class MobileExecutor:
    """移动端测试执行器"""

    def __init__(self):
        self.android_pool = AndroidDevicePool()
        self.ios_pool = IOSDevicePool()

    async def execute_android_test(
        self,
        run_id: str,
        device_id: str,
        test_code: str,
        app_path: str
    ) -> dict:
        """执行Android测试"""
        device = await self.android_pool.acquire_device(device_id)

        try:
            # 启动Appium服务器
            appium_server = await AppiumServerAndroid.start(device)

            # 执行测试
            result = await self._run_appium_test(
                appium_server.url,
                device.capabilities,
                test_code,
                app_path
            )

            # 捕获截图
            screenshots = await self._capture_screenshots(device)

            return {
                "status": "success",
                "device": device.serial,
                "screenshots": screenshots,
                "result": result
            }
        finally:
            await self.android_pool.release_device(device)
            await appium_server.stop()

    async def execute_ios_test(
        self,
        run_id: str,
        device_id: str,
        test_code: str,
        app_path: str
    ) -> dict:
        """执行iOS测试"""
        device = await self.ios_pool.acquire_device(device_id)

        try:
            # 启动WDA (WebDriverAgent)
            wda = await WDA.start(device)

            # 执行测试
            result = await self._run_xCUITest(
                wda.url,
                device.capabilities,
                test_code,
                app_path
            )

            screenshots = await self._capture_screenshots(device)

            return {
                "status": "success",
                "device": device.uuid,
                "screenshots": screenshots,
                "result": result
            }
        finally:
            await self.ios_pool.release_device(device)
            await wda.stop()

class AndroidDevicePool:
    """Android设备池"""

    def __init__(self):
        self.available = []
        self.busy = {}

    async def acquire_device(self, device_id: str = None) -> Device:
        """获取可用设备"""
        if device_id:
            device = self._get_device_by_id(device_id)
        else:
            device = self._get_any_available()

        device.status = "busy"
        self.busy[device.serial] = device
        return device

    def _get_device_by_id(self, device_id: str) -> Device:
        # 查询数据库获取设备
        ...

class IOSDevicePool:
    """iOS设备池"""
    # 类似实现，使用XCRun管理模拟器
```

#### `backend/app/services/device_service.py` - 设备管理服务（新增）
```python
# 实现思路：
# 1. Android设备：通过ADB连接设备，管理设备状态
# 2. iOS设备：通过XCRun管理模拟器，通过XCDevice管理真机
# 3. Appium服务器：为每台设备启动/停止Appium实例
# 4. 设备发现：自动发现局域网内的移动设备

class DeviceService:
    """设备管理服务"""

    async def discover_android_devices(self) -> list:
        """发现Android设备"""
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        devices = []
        for line in result.stdout.strip().split("\n")[1:]:
            if line.strip():
                serial, status = line.split("\t")
                devices.append({
                    "serial": serial,
                    "status": status,
                    "platform": "android"
                })
        return devices

    async def discover_ios_devices(self) -> list:
        """发现iOS设备"""
        result = subprocess.run(["xcrun", "simctl", "list", "devices"], capture_output=True, text=True)
        # 解析输出获取模拟器列表
        ...

    async def connect_device(self, device_info: dict) -> Device:
        """连接设备"""
        device = Device(
            serial=device_info["serial"],
            platform=device_info["platform"],
            status="online"
        )
        await device.save()
        return device

    async def start_appium_for_device(self, device: Device) -> str:
        """为设备启动Appium服务器"""
        port = self._allocate_port()
        subprocess.Popen([
            "appium",
            "--port", str(port),
            "--bootstrap-port", str(port + 1),
            "-U", device.serial,
            "--device-name", device.model,
            "--platform-name", device.platform.upper(),
            "--platform-version", device.os_version
        ])
        return f"http://localhost:{port}"

    async def get_device_screen(self, device: Device) -> bytes:
        """获取设备当前屏幕截图"""
        if device.platform == "android":
            result = subprocess.run([
                "adb", "-s", device.serial, "exec-out", "screencap", "-p"
            ], capture_output=True)
        else:
            result = subprocess.run([
                "xcrun", "simctl", "io", device.uuid, "screenshot"
            ], capture_output=True)
        return result.stdout
```

### 2.2 前端核心文件实现

#### `frontend/src/App.tsx` - 应用入口
```tsx
// 实现思路：
// 1. 配置React Router路由
// 2. 状态管理Provider（Zustand）
// 3. 全局样式配置
// 4. 权限控制：高阶组件校验登录状态和项目权限

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { ConfigProvider } from "antd"
import { useUserStore } from "./store/userStore"
import BasicLayout from "./layouts/BasicLayout"

function App() {
  return (
    <ConfigProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/projects" />} />
          <Route path="/projects/*" element={<BasicLayout />} />
          {/* 其他路由 */}
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}
```

#### `frontend/src/pages/TestExecution/index.tsx` - 执行监控页
```tsx
// 实现思路：
// 1. 执行列表：展示所有测试执行记录
// 2. 设备选择：下拉选择Android/iOS设备
// 3. 执行控制：开始、停止、重试按钮
// 4. 实时日志：WebSocket接收日志流
// 5. 进度展示：时间线显示执行阶段

import { useWebSocket } from "@/hooks/useWebSocket"
import { useAsyncRun } from "@/hooks/useAsyncRun"
import { ExecutionLog } from "@/components/ExecutionLog"

export function TestExecutionPage() {
  const { logs, connect, disconnect } = useWebSocket(`/ws/execution/{runId}`)
  const { data: runList } = useRequest(() => api.getTestRuns())

  return (
    <div>
      <Card>
        <Space>
          <DeviceSelector platform="android" />
          <DeviceSelector platform="ios" />
          <Button type="primary" onClick={handleStart}>开始执行</Button>
        </Space>
      </Card>

      <Row gutter={16}>
        <Col span={16}>
          <ExecutionLog logs={logs} />
        </Col>
        <Col span={8}>
          <ExecutionProgress runId={runId} />
        </Col>
      </Row>
    </div>
  )
}
```

#### `frontend/src/components/DeviceSelector/index.tsx` - 设备选择器
```tsx
// 实现思路：
// 1. 平台切换：Android / iOS Tab
// 2. 设备列表：展示可用设备（图标区分真机/模拟器）
// 3. 状态标识：在线/忙碌/离线
// 4. 选中态：高亮当前选中的设备

export function DeviceSelector({ platform, value, onChange }) {
  const { data: devices } = useRequest(() => api.getDevices(platform))

  return (
    <Tabs defaultActiveKey={platform}>
      <Tabs.TabPane key="android" tab="Android">
        <List
          dataSource={devices?.filter(d => d.platform === "android")}
          renderItem={(device) => (
            <List.Item
              className={device.status === "busy" ? "disabled" : ""}
              onClick={() => device.status !== "busy" && onChange(device.id)}
            >
              <Avatar icon={device.device_type === "real_device" ? <MobileIcon /> : <LaptopIcon />} />
              <span>{device.name}</span>
              <Tag color={device.status === "online" ? "green" : "red"}>{device.status}</Tag>
            </List.Item>
          )}
        />
      </Tabs.TabPane>
      <Tabs.TabPane key="ios" tab="iOS">
        {/* iOS设备列表 */}
      </Tabs.TabPane>
    </Tabs>
  )
}
```

### 2.3 沙箱执行器实现

#### `sandbox/executor/run_mobile_test.py` - 移动端测试执行器
```python
# 实现思路：
# 1. 接收测试代码和设备信息
# 2. 安装被测App（APK/IPA）
# 3. 执行Appium测试脚本
# 4. 捕获测试截图和日志
# 5. 解析测试结果（JUnit XML）
# 6. 上报结果到后端

import sys
import json
import subprocess
from pathlib import Path

def run_mobile_test(platform: str, device_serial: str, test_code: str, app_path: str):
    """执行移动端测试"""

    # 安装App
    if platform == "android":
        subprocess.run(["adb", "-s", device_serial, "install", "-r", app_path])
    else:
        subprocess.run(["xcrun", "simctl", "install", "booted", app_path])

    # 执行测试
    result = subprocess.run([
        "python", "-m", "pytest",
        test_code,
        "--platform", platform,
        "--device", device_serial,
        "--html=report.html",
        "--self-contained-html"
    ], capture_output=True, text=True)

    # 截图目录
    screenshot_dir = Path("screenshots")
    screenshots = list(screenshot_dir.glob("*.png"))

    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "output": result.stdout,
        "screenshots": [str(s) for s in screenshots]
    }

if __name__ == "__main__":
    params = json.loads(sys.argv[1])
    result = run_mobile_test(**params)
    print(json.dumps(result))
```

---

## 三、数据库设计（支持移动端）

### 3.1 新增/修改表结构

```sql
-- 设备表（新增）
CREATE TABLE devices (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    platform ENUM('android', 'ios') NOT NULL,
    device_type ENUM('real_device', 'emulator', 'simulator') NOT NULL,
    serial VARCHAR(100),                -- ADB serialno / iOS uuid
    appium_port INT,
    wda_port INT,                       -- iOS WDA端口
    status ENUM('online', 'offline', 'busy', 'maintaining') DEFAULT 'offline',
    current_run_id VARCHAR(36),
    os_version VARCHAR(20),
    manufacturer VARCHAR(50),
    model VARCHAR(50),
    capabilities JSON,                  -- Appium capabilities
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 测试执行记录表（新增字段）
ALTER TABLE test_runs ADD COLUMN device_id VARCHAR(36);
ALTER TABLE test_runs ADD COLUMN platform ENUM('web', 'api', 'android', 'ios');

-- 测试代码表（新增字段）
ALTER TABLE test_code ADD COLUMN platform ENUM('web', 'android', 'ios');
ALTER TABLE test_code ADD COLUMN app_path VARCHAR(500);  -- App包路径

-- 项目配置表（扩展）
ALTER TABLE projects MODIFY COLUMN config JSON;
-- config示例：
-- {"test_types": ["web", "android", "ios"], "default_framework": "pytest", "android_package": "com.example.app", "ios_bundle": "com.example.app"}
```

---

## 四、后端API设计

### 4.1 设备管理 `/api/v1/devices`（新增）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | / | 获取设备列表 |
| POST | /discover | 发现新设备 |
| POST | /connect | 连接设备 |
| DELETE | /{device_id} | 断开设备 |
| GET | /{device_id}/screen | 获取设备截图 |
| POST | /{device_id}/start-appium | 启动Appium服务器 |
| POST | /{device_id}/stop-appium | 停止Appium服务器 |

### 4.2 移动端测试 `/api/v1/test-runs/mobile`

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | / | 创建移动端测试执行 |
| GET | /{run_id}/device-screen | 实时获取设备屏幕 |

---

## 五、技术风险识别与验证计划

### 5.1 技术风险矩阵

| 风险类别 | 风险点 | 严重程度 | 发生概率 | 应对策略 |
|---------|--------|---------|---------|---------|
| **移动端-A** | iOS测试只能在macOS运行 | 🔴 高 | 100% | 使用macOS物理机或云macOS服务 |
| **移动端-B** | Android模拟器需要特殊虚拟化支持 | 🟡 中 | 60% | 使用真机 + adb网络连接 |
| **移动端-C** | 不同Android版本的Appium兼容性差异 | 🟡 中 | 60% | 限制支持版本（Android 10-13） |
| **AI能力-A** | AI生成的代码可运行率低于预期 | 🟡 中 | 50% | 保留人工编辑功能作为兜底 |
| **AI能力-B** | AI影响分析准确率不足 | 🟡 中 | 50% | 提供手动确认环节 |
| **AI能力-C** | 多模型切换后输出格式不一致 | 🟡 中 | 30% | 统一后处理解析逻辑 |
| **架构-A** | WebSocket高并发下内存泄漏 | 🟡 中 | 30% | 使用Redis Pub/Sub中转 |
| **集成-A** | Git API（GitHub/GitLab/Gitee）接口差异 | 🟡 中 | 40% | 适配器模式封装 |

> **注意**：Docker沙箱仅用于Web/接口自动化测试，**不用于移动端测试**。移动端测试由宿主机直接控制的Appium服务执行。

### 5.2 技术验证优先级

#### 🔴 P0 - 核心风险（必须优先验证，验证失败则项目无法推进）

| 优先级 | 序号 | 技术点 | 验证方法 | 通过标准 |
|--------|------|--------|----------|---------|
| P0-1 | **V1** | FastAPI异步性能 | 压测100并发CRUD | QPS > 500 |
| P0-2 | **V2** | MySQL JSON字段 | 存储10万条，索引查询 | 查询 < 100ms |
| P0-3 | **V5** | Android真机连接 | adb网络连接 + 截图 | 截图成功 |
| P0-4 | **V6** | Appium Android | 执行简单测试用例 | 测试通过，截图成功 |
| P0-5 | **V7** | Appium iOS | 执行XCUITest | 测试通过，截图成功 |

#### 🟡 P1 - 重要功能（验证失败有备选方案，不阻断项目）

| 优先级 | 序号 | 技术点 | 验证方法 | 通过标准 | 备选方案 |
|--------|------|--------|----------|---------|---------|
| P1-1 | V3 | Redis缓存 | 相同输入重复请求 | 缓存命中 | 降级到内存缓存 |
| P1-2 | V4 | Docker沙箱-Web | 创建+执行+销毁循环 | < 30秒 | 本地进程池 |
| P1-3 | V8 | AI用例生成 | 输入10个需求评估 | 可运行率 > 70% | 用例模板+人工微调 |
| P1-4 | V9 | AI影响分析 | 修改5个需求后测试 | 召回率 > 60% | 辅助分析模式 |
| P1-5 | V10 | AI代码修复 | 修改5个需求后修复 | 可运行率 > 70% | 人工编辑兜底 |
| P1-6 | V11 | AI模型稳定性 | 连续100次调用 | 成功率 > 99% | 多模型切换 |

#### 🟢 P2 - 辅助功能（可延后验证）

| 优先级 | 序号 | 技术点 | 验证方法 | 通过标准 |
|--------|------|--------|----------|---------|
| P2-1 | V12 | WebSocket推送 | 执行时测量延迟 | < 1秒 |
| P2-2 | V13 | Git对接 | 对接GitHub/GitLab/Gitee | diff解析正确 |
| P2-3 | V14 | 多项目隔离 | 跨项目查询 | 无数据泄露 |
| P2-4 | V15 | 报告导出 | 导出PDF/HTML | 文件可打开 |

### 5.3 技术验证执行计划

#### Day 1-2: P0核心风险验证（🔴 最关键）

```
上午：基础环境搭建
- Docker + MySQL + Redis + FastAPI
- Android真机（开启USB调试 + 网络ADB）

下午：P0-1 ~ P0-4 验证
- V1: FastAPI异步QPS测试
- V2: MySQL JSON查询测试
- V5: Android adb connect网络连接 + 截图
- V6: Appium Android执行简单测试
```

```
Day 2 下午：P0-5 验证（如果无macOS可跳过）
- V7: Appium iOS测试（必须在macOS上）
- 若验证失败：记录"阶段一只支持Android"
```

**Day 2 结束：核心风险评审**
```
输出：
- [ ] V1通过 / [ ] V1失败（备选方案：同步框架）
- [ ] V2通过 / [ ] V2失败（备选方案：拆分字段）
- [ ] V5通过 / [ ] V5失败（备选方案：USB直连）
- [ ] V6通过 / [ ] V6失败（备选方案：限制Android版本）
- [ ] V7通过 / [ ] V7失败（决策：延后iOS支持）
```

#### Day 3-4: P1重要功能验证

```
Day 3:
- V3: Redis缓存测试
- V4: Docker沙箱Web测试执行
- V8: AI用例生成质量评估（DeepSeek + GPT-4o）

Day 4:
- V9: AI影响分析准确率评估
- V10: AI代码修复可运行率评估
- V11: AI模型稳定性压测
```

**Day 4 结束：重要功能评审**
```
输出：
- AI能力评估报告（是否需要人工编辑兜底）
- Docker沙箱验证结果
```

#### Day 5: P2辅助功能 + 架构集成验证

```
上午：
- V12: WebSocket实时推送测试
- V13: Git对接测试

下午：
- V14: 多项目数据隔离验证
- V15: 报告导出测试
```

#### Day 5 下午：技术验证总结会议

```
输出：
1. 技术验证报告（P0/P1/P2通过情况）
2. 风险登记册（已识别风险+应对策略）
3. 阶段一开发计划（根据验证结果调整）
4. 关键技术决策记录
```

### 5.4 验证环境要求

| 验证项 | 环境要求 | 准备事项 |
|--------|---------|---------|
| V1, V2 | Linux服务器 + MySQL + Redis | Docker环境 |
| V3, V5, V6 | Android真机 + 网络可达 | 一台开启USB调试的Android手机 |
| V7 | macOS机器 | Mac电脑 + iPhone/iPad（可选模拟器） |
| V4 | Docker沙箱 | Python + pytest环境镜像 |
| V8-V11 | AI API | DeepSeek/GPT-4o API密钥 |

### 5.5 技术验证检查清单

#### 🔴 P0 核心风险（必须全部通过）
- [ ] V1: FastAPI异步QPS > 500
- [ ] V2: MySQL JSON查询 < 100ms
- [ ] V5: Android adb connect网络连接成功
- [ ] V6: Appium Android测试通过
- [ ] V7: Appium iOS测试通过（或确认需要macOS）

#### 🟡 P1 重要功能
- [ ] V3: Redis缓存命中
- [ ] V4: Docker沙箱Web测试 < 30秒
- [ ] V8: AI用例可运行率 > 70%
- [ ] V9: AI影响分析召回率 > 60%
- [ ] V10: AI代码修复可运行率 > 70%
- [ ] V11: AI API成功率 > 99%

#### 🟢 P2 辅助功能
- [ ] V12: WebSocket延迟 < 1秒
- [ ] V13: Git对接成功
- [ ] V14: 多项目隔离验证
- [ ] V15: 报告导出正常

Week 2: 全流程集成测试
```

#### 阶段五：优化与部署（1周）

```
- 性能优化
- Docker Compose部署
- 文档完善
```

### 5.4 关键技术验证代码

```python
# V1: FastAPI异步性能验证
import asyncio
import time
from locust import HttpUser, task, between

async def test_concurrent_crud():
    """验证异步数据库QPS"""
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine("mysql+aiomysql://user:pass@host:3306/db", pool_size=20)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def create_project():
        start = time.time()
        async with async_session() as session:
            project = Project(name="test")
            session.add(project)
            await session.commit()
        return time.time() - start

    # 并发100请求
    tasks = [create_project() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    avg_time = sum(results) / len(results)
    qps = 100 / sum(results)
    print(f"QPS: {qps}, Avg: {avg_time}s")  # 目标 QPS > 500

# V5: Android真机ADB网络连接验证
def test_adb_network_connection():
    """验证Docker沙箱能否通过网络控制Android真机"""
    import subprocess

    # 1. Android真机开启网络ADB (adb tcpip 5555)
    # 2. 在沙箱中执行 adb connect
    result = subprocess.run(
        ["adb", "connect", "192.168.1.100:5555"],
        capture_output=True, text=True
    )
    print(result.stdout)  # 期望: "connected to 192.168.1.100:5555"

    # 3. 截图验证
    result = subprocess.run(
        ["adb", "-s", "192.168.1.100:5555", "exec-out", "screencap", "-p"],
        capture_output=True
    )
    assert len(result.stdout) > 1000, "截图失败"
    print(f"截图成功: {len(result.stdout)} bytes")

# V6: Appium Android验证
def test_appium_android():
    """验证Appium能否控制Android真机"""
    from appium import webdriver
    from appium.webdriver.extensions.android.nativekey import AndroidKey

    desired_caps = {
        "platformName": "Android",
        "deviceName": "TestDevice",
        "udid": "192.168.1.100:5555",  # 网络连接的设备
        "automationName": "UiAutomator2",
        "noReset": True,
        "newCommandTimeout": 300
    }

    driver = webdriver.Remote("http://appium:4723/wd/hub", desired_caps)

    # 简单测试：打开设置
    driver.start_activity("com.android.settings", ".SettingsActivity")
    time.sleep(2)

    # 截图
    driver.save_screenshot("/tmp/screenshot.png")
    driver.quit()
    print("Appium Android测试成功")

# V7: Appium iOS验证
def test_appium_ios():
    """验证Appium iOS（必须在macOS上运行）"""
    # 注意：此测试只能在macOS上运行
    from appium import webdriver

    desired_caps = {
        "platformName": "iOS",
        "deviceName": "iPhone 15 Pro",
        "platformVersion": "17.0",
        "automationName": "XCUITest",
        "app": "/path/to/app.app",
        "useNewWDA": True
    }

    driver = webdriver.Remote("http://localhost:4723/wd/hub", desired_caps)
    driver.find_element_by_accessibility_id("SomeID").click()
    driver.get_screenshot_as_file("/tmp/screenshot.png")
    driver.quit()

# V8: AI用例生成质量评估
async def test_ai_case_generation():
    """评估AI生成的测试用例质量"""
    ai_service = AIService("deepseek-v2")

    test_requirements = [
        "用户登录：输入正确用户名密码跳转首页，输入错误显示错误提示",
        "商品列表：分页展示商品，每页20个，支持下拉刷新",
        "订单提交：选择地址和支付方式，生成订单"
    ]

    results = []
    for req in test_requirements:
        output = await ai_service.analyze_requirement(req, "")
        cases = json.loads(output)["test_cases"]

        # 验证用例结构完整性
        valid = all(
            "case_id" in c and "title" in c and "steps" in c
            for c in cases
        )
        results.append({"req": req, "cases": cases, "valid": valid})

    # 统计可运行率（需要实际执行验证）
    print(f"生成质量: {sum(r['valid'] for r in results)/len(results)*100}%")
```

### 5.5 关键风险应对决策树

```
                    技术验证失败？
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      V5/V6失败       V7失败          V8/V10失败
     (Android)        (iOS)         (AI能力)
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐    ┌───────────┐    ┌──────────┐
    │改用USB  │    │阶段一只   │    │增加人工  │
    │直连（需 │    │支持Android│    │编辑兜底  │
    │物理接触）│    │后续再支持 │    │提高AI质量│
    └─────────┘    │iOS        │    └──────────┘
                   └───────────┘
```

### 5.6 技术验证输出物

| 输出物 | 内容 | 责任人 |
|-------|------|-------|
| 技术验证报告 | 每个验证点的测试方法、结果、结论 | 技术负责人 |
| 风险登记册 | 已识别风险、应对策略、责任人 | 项目经理 |
| 开发计划调整 | 根据验证结果调整的阶段计划 | 技术负责人 |
| 技术方案评审 | 关键技术方案评审（架构、AI、移动端） | 技术负责人 |

### 5.7 技术验证检查清单（Checklist）

- [ ] V1: FastAPI异步QPS > 500
- [ ] V2: MySQL JSON查询 < 100ms
- [ ] V3: Redis缓存命中
- [ ] V4: Docker沙箱Web测试 < 30秒
- [ ] V5: Android adb connect成功
- [ ] V6: Appium Android测试通过
- [ ] V7: Appium iOS测试通过（或确认需要macOS）
- [ ] V8: AI用例可运行率 > 70%
- [ ] V9: AI影响分析召回率 > 60%
- [ ] V10: AI代码修复可运行率 > 70%
- [ ] V11: AI API成功率 > 99%
- [ ] V12: WebSocket延迟 < 1秒
- [ ] V13: Git对接成功
- [ ] V14: 多项目隔离验证
- [ ] V15: 报告导出正常

---

## 六、关键技术点

### 6.1 移动端测试关键技术

1. **Android真机测试**
   - ADB连接管理：设备发现、端口映射、屏幕截图
   - Appium UiAutomator2：元素定位、交互操作
   - APK安装与卸载：adb install / adb uninstall

2. **iOS测试**
   - XCRun：模拟器管理
   - XCUITest：原生iOS自动化框架
   - WebDriverAgent (WDA)：iOS的Appium底层驱动
   - XCTest：Apple官方测试框架

3. **Appium跨平台**
   - 统一脚本：Python+Appium可同时支持Android/iOS
   - 元素定位：Accessibility ID、XPath、坐标
   - 混合应用测试：原生控件 + WebView切换

### 6.2 AI能力关键技术

1. **多模型切换**
   - 适配器模式封装不同模型API
   - 统一返回格式
   - 故障转移：模型A失败自动切换B

2. **提示词工程**
   - Few-shot Learning：提供示例提高输出质量
   - 结构化输出：强制JSON格式便于解析
   - 角色设定：明确AI扮演测试工程师角色

3. **代码修复**
   - 上下文理解：输入旧代码+新需求+变更diff
   - 最小修改：只改失效部分，保留有效部分
   - 语法验证：生成后校验Python/Swift语法

### 6.3 性能优化

1. **数据库**
   - 连接池：aiomysql + pool_pre_ping
   - 索引：project_id, requirement_id, status
   - 分页：游标分页避免大偏移量

2. **缓存**
   - Redis：AI响应缓存、项目列表缓存
   - 缓存策略：LRU + TTL过期

3. **异步任务**
   - Celery/Redis Queue：测试执行任务队列
   - Worker池：多个worker并发执行

---

## 七、开发阶段规划

| 阶段 | 周期 | 内容 | 关键里程碑 |
|------|------|------|-----------|
| **阶段零** | **1周** | **技术可行性验证** 🔴 | P0全部通过，风险登记册完成 |
| 阶段一 | 2周 | 项目脚手架、数据库、基础CRUD API | 基础API可用 |
| 阶段二 | 2周 | 需求管理、Git对接、AI服务集成 | AI服务接入完成 |
| 阶段三 | 2周 | AI影响分析、自动修复代码 | AI功能完成 |
| 阶段四 | 2周 | 测试代码生成、执行引擎 | 执行引擎可用 |
| 阶段五 | 2周 | 报告系统、前端UI完善 | 前端功能完整 |
| 阶段六 | 1周 | Docker部署、集成测试 | 可部署版本 |

**总计：约12周**

**关键路径**：阶段零 → 阶段一 → 阶段二 → 阶段四 → 阶段六

---

## 八、架构决策记录

### 8.1 Docker沙箱适用范围

| 测试类型 | 是否在Docker中运行 | 原因 |
|---------|-------------------|------|
| 接口自动化 | ✅ 是 | 环境隔离、快速创建销毁、无硬件依赖 |
| Web UI自动化 | ✅ 是 | 浏览器环境隔离、无硬件依赖 |
| Android真机 | ❌ 否 | 必须直接访问USB设备 |
| Android模拟器 | ❌ 否 | 需要特殊虚拟化支持 |
| iOS真机 | ❌ 否 | 只能在macOS运行 |
| iOS模拟器 | ❌ 否 | 只能在macOS运行 |

### 8.2 移动端测试架构

```
┌─────────────────────────────────────────────────────────────┐
│  测试平台 Backend (FastAPI)                                 │
│                                                             │
│  调度服务                                                    │
│      │                                                      │
│      ├── Web/接口测试 → Docker Worker Pool                   │
│      │                      (沙箱隔离执行)                    │
│      │                                                      │
│      └── 移动端测试 → Appium Server (宿主机)                  │
│                         │                                   │
│                ┌────────┴────────┐                         │
│                ▼                 ▼                          │
│         Android设备          iOS设备                         │
│         (adb网络连接)         (macOS+WDA)                   │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 关键决策

| 决策项 | 决策内容 | 决策时间 |
|--------|---------|---------|
| Docker沙箱范围 | 仅用于Web/接口测试，不用于移动端 | 技术验证阶段 |
| iOS支持时机 | 阶段一只支持Android，iOS根据macOS资源情况决定 | 技术验证后 |
| AI兜底策略 | AI能力不足时保留人工编辑功能 | 阶段二开发时 |
