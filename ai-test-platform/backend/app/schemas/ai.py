from typing import Optional, Any
from pydantic import BaseModel


class AnalyzeRequirementRequest(BaseModel):
    requirement_title: str
    requirement_description: str


class AnalyzeRequirementResponse(BaseModel):
    test_points: list[Any]  # AI 返回的结构化数据
    risk_points: list[Any]
    suggested_test_types: list[str]
    raw_response: Optional[str] = None


class GenerateTestCasesRequest(BaseModel):
    requirement_title: str
    requirement_description: str
    test_types: list[str] = ["web"]


class GenerateTestCodeRequest(BaseModel):
    test_cases: list[dict]
    framework: str = "pytest"


class GenerateTestCodeResponse(BaseModel):
    code: str


class AnalyzeCodeImpactRequest(BaseModel):
    code_changes: list[dict]
    requirements: list[dict]


class ChatRequest(BaseModel):
    messages: list[dict]
    temperature: float = 0.7


class ChatResponse(BaseModel):
    content: str
