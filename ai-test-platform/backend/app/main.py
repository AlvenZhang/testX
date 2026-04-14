from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import projects, requirements, code_changes, ai, test_cases, test_plans, test_runs, reports, workflows, executions, test_code
from .core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    print(f"Starting {settings.app_name}")
    yield
    print("Shutting down...")


app = FastAPI(
    title="AI Test Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(requirements.router, prefix="/api/v1")
app.include_router(code_changes.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(test_cases.router, prefix="/api/v1")
app.include_router(test_plans.router, prefix="/api/v1")
app.include_router(test_runs.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(executions.router, prefix="/api/v1")
app.include_router(test_code.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
