# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI-powered multi-project automated testing platform** that automates the flow from "requirements + code changes" to "test execution + regression testing". The project is currently in **technical verification phase (Phase 0)** - the actual implementation code does not exist yet.

### Core Technology Stack
- **Backend**: FastAPI + Python 3.11+ (async)
- **Frontend**: React 18 + TypeScript + Ant Design (planned)
- **Database**: MySQL 8.0 (with JSON fields)
- **Cache**: Redis 6.0+
- **Mobile Testing**: Appium (Android UiAutomator2 + iOS XCUITest)
- **AI Models**: GPT-4o / DeepSeek-v2 / Qwen (multi-model support via adapter pattern)
- **Test Execution**: Docker sandbox isolation (Web/API tests only)

### Key Architecture Decision
- **Docker sandbox**: Only for Web and API automated tests (environment isolation)
- **Mobile tests**: Run directly on host with Appium (not in Docker) due to USB/device hardware dependencies
- **iOS testing**: Requires macOS (cannot run on Linux servers)

---

## Repository Structure

```
ai-test-platform/          # Planned - not yet created
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/v1/        # API routes (projects, requirements, test_cases, etc.)
│   │   ├── core/          # Config, security, database
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/      # Business logic (AI, git, test executor, mobile)
│   │   └── workers/       # Async task workers
│   └── tests/             # Backend tests
├── frontend/              # React TypeScript app (planned)
├── sandbox/               # Docker test execution sandbox
│   ├── docker/            # Dockerfile for test environment
│   └── executor/          # Test executors (api, web, mobile)
├── android-device-farm/   # ADB + Appium Android management
├── ios-device-farm/       # XCRun + Appium iOS management
└── docker-compose.yml

技术验证/                    # Current work: P0 technical verification
├── 01-P0核心验证/          # P0 core risk verification scripts
│   ├── verify_v1_fastapi_performance.py
│   ├── verify_v2_mysql_json.py
│   ├── verify_v5_android_adb.py
│   ├── verify_v6_appium_android.py
│   └── verify_v7_appium_ios.py
└── requirements.txt
```

---

## Current Work: P0 Technical Verification

The repository is in the verification phase. **Do not build features** - focus on verifying the technical risks.

### P0 Verification Scripts (run in order)

| Verification | Script | Success Criteria |
|-------------|--------|-------------------|
| V1: FastAPI async performance | `verify_v1_fastapi_performance.py` | QPS > 500 |
| V2: MySQL JSON fields | `verify_v2_mysql_json.py` | Query < 100ms |
| V5: Android ADB network | `verify_v5_android_adb.py` | Screenshot succeeds |
| V6: Appium Android | `verify_v6_appium_android.py` | Test passes, screenshot succeeds |
| V7: Appium iOS | `verify_v7_appium_ios.py` | Test passes (macOS only) |

### Running P0 Verification

```bash
cd 技术验证/01-P0核心验证

# Install dependencies
pip install -r ../requirements.txt

# Run all P0 verifications
./run_p0_verification.sh

# Or run individually
python verify_v1_fastapi_performance.py
python verify_v2_mysql_json.py
```

### P0 Verification Environment Requirements

| Verification | Environment |
|-------------|-------------|
| V1, V2 | Linux server + MySQL 8.0 + Redis |
| V3, V5, V6 | Android device with USB debugging enabled + network ADB |
| V7 | macOS machine with Xcode + iOS device/simulator |

---

## Database Design Notes

- **projects.config**: JSON field storing test_types (web/android/ios), default_framework, etc.
- **devices table**: Manages Android/iOS real devices and emulators with status (online/offline/busy)
- **test_runs**: Extended with device_id and platform columns for mobile testing
- **JSON fields used for**: project config, test case metadata, device capabilities

---

## Key Services (Planned)

| Service | Responsibility |
|---------|----------------|
| `ai_service.py` | Multi-model AI adapter (GPT-4o/DeepSeek/Qwen), handles chat, requirement analysis, impact analysis, code fixing |
| `test_executor.py` | Docker sandbox lifecycle management for Web/API tests |
| `mobile_executor.py` | Appium server management, device pool for Android/iOS |
| `device_service.py` | ADB device discovery, XCRun simulator management |
| `impact_service.py` | AI-powered regression test impact analysis |

---

## Mobile Testing Architecture

```
Backend (FastAPI)
    ├── Web/API tests → Docker Worker Pool (sandbox isolation)
    │
    └── Mobile tests → Appium Server (host machine)
                           ├── Android → adb connect (network) or USB
                           └── iOS → macOS + WebDriverAgent (WDA)
```

---

## Environment Variables

See `技术验证/.env.example` for required environment variables. Key variables:
- `DATABASE_URL`: MySQL connection string
- `REDIS_URL`: Redis connection string
- `AI_MODEL_NAME`: Model selection (deepseek-v2, gpt-4o, qwen)
- `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `ALIYUN_API_KEY`: AI model API keys

---

## Coding Standards

### Package Management: uv

**All Python dependency management MUST use `uv`. Never use `pip` directly.**

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add fastapi httpx

# Add a dev dependency
uv add --dev pytest pytest-asyncio

# Update dependencies
uv update

# Create a frozen lock file for reproducible builds
uv lock --locked

# Install in editable mode (for local development)
uv pip install -e .

# Sync dependencies to match pyproject.toml
uv sync
```

### Python Code Style

| Rule | Standard |
|------|----------|
| **Formatter** | Ruff formatter (auto-format on save) |
| **Line length** | 120 characters |
| **Indentation** | 4 spaces |
| **Type hints** | Strict mode - all function signatures MUST have type hints |
| **Async** | Use `async/await` for all I/O operations; never mix sync/async |
| **Naming** | `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE` constants |

### Type Hints (Strict)

```python
# GOOD - complete type hints
async def get_project(project_id: str) -> Project | None:
    ...

# BAD - missing type hints
async def get_project(project_id):
    ...
```

### Async Patterns

```python
# GOOD - proper async context
async with async_session() as session:
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()

# GOOD - gather for parallel operations
results = await asyncio.gather(
    fetch_requirements(project_id),
    fetch_test_cases(project_id),
    fetch_devices()
)

# BAD - blocking call in async function
def sync_operation():
    return blocking_db_call()  # Never do this

# BAD - not using await for async calls
async def bad_example():
    results = asyncio.gather(...)  # Missing await
```

### SQLAlchemy Patterns

```python
# Use async engine
engine = create_async_engine(DATABASE_URL, pool_size=20, pool_pre_ping=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Always use context manager for sessions
async with async_session() as session:
    ...

# JSON fields for flexible schema
config: Mapped[dict[str, Any]] = Column(JSON)
```

### FastAPI Patterns

```python
# Use dependency injection for database sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Pydantic models for request/response (in schemas/)
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    config: dict[str, Any] | None = None

# Use status codes explicitly
from fastapi import status
return JSONResponse(status_code=status.HTTP_201_CREATED, content=result)

# Lifespan context manager (not deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_resources()
    yield
    await cleanup_resources()
```

### Mobile Testing (Appium)

```python
# Android - use UiAutomator2
desired_caps = {
    "platformName": "Android",
    "automationName": "UiAutomator2",
    "udid": "192.168.1.100:5555",  # Network ADB
    "noReset": True,
}

# iOS - use XCUITest
desired_caps = {
    "platformName": "iOS",
    "automationName": "XCUITest",
    "useNewWDA": True,
}

# Always quit in finally block
try:
    driver = webdriver.Remote(...)
    ...
finally:
    driver.quit()
```

### AI Service Patterns

```python
# Adapter pattern for multi-model support
class AIModelAdapter(ABC):
    @abstractmethod
    async def chat(self, messages: list[ChatMessage], **kwargs) -> str:
        pass

# Retry with exponential backoff
@async_retry(max_attempts=3, base_delay=1.0)
async def call_ai_model(prompt: str) -> str:
    ...

# Cache AI responses in Redis
cache_key = f"ai:response:{hashlib.md5(prompt.encode()).hexdigest()}"
cached = await redis.get(cache_key)
if cached:
    return cached
```

### Error Handling

```python
# Use custom exceptions with explicit messages
class DeviceNotFoundError(Exception):
    pass

# Handle gracefully with appropriate HTTP status codes
async def get_device(device_id: str) -> Device:
    device = await device_service.get(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found"
        )
    return device

# Always clean up resources in finally/async with
try:
    container = await create_sandbox()
    result = await run_tests(container)
finally:
    await destroy_sandbox(container)
```

### Testing

```python
# Use pytest-asyncio for async tests
import pytest

@pytest.mark.asyncio
async def test_project_creation():
    project = await create_project(name="Test")
    assert project.name == "Test"

# Use fixtures for shared setup
@pytest.fixture
async def db_session():
    async with async_session() as session:
        yield session

# Test file naming: test_<module>.py
# Test class naming: Test<ModuleName>
# Test function naming: test_<description>
```

### Pre-commit Hooks

```bash
# Install pre-commit
uv add --dev pre-commit

# Run manually
pre-commit run --all-files

# Or let uv handle it via pre-commit integration
```

### File Organization

```
backend/
├── app/
│   ├── __init__.py           # Empty or exports FastAPI app
│   ├── main.py               # FastAPI app factory
│   ├── api/                  # API routes only
│   │   └── v1/
│   │       └── projects.py   # One file per resource
│   ├── core/                 # Config, security, database (no business logic)
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/               # SQLAlchemy models (data only)
│   ├── schemas/              # Pydantic models (API contracts)
│   ├── services/             # Business logic (async)
│   └── utils/               # Pure utility functions
└── tests/
    ├── conftest.py          # pytest fixtures
    ├── api/                 # API integration tests
    └── services/            # Service unit tests
```

### Import Order (enforced by Ruff)

1. Standard library
2. Third-party packages
3. Local application imports

```python
# Standard library
import asyncio
import hashlib
from datetime import datetime

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Local application
from app.core.config import Settings
from app.models.project import Project
```

### What to Avoid

- **DO NOT** use `pip install` - use `uv add`
- **DO NOT** use `async def` with sync I/O (blocking the event loop)
- **DO NOT** use bare `except:` - catch specific exceptions
- **DO NOT** commit API keys, tokens, or credentials
- **DO NOT** use `Table.do_*` methods (use service layer)
- **DO NOT** create "util" modules with mixed responsibilities - organize by domain
- **DO NOT** write code that doesn't pass type checking with `mypy`
