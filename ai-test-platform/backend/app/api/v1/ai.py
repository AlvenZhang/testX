from fastapi import APIRouter, HTTPException

from ...services.ai_service import get_ai_service
from ...schemas.ai import (
    AnalyzeRequirementRequest, AnalyzeRequirementResponse,
    GenerateTestCasesRequest,
    GenerateTestCodeRequest, GenerateTestCodeResponse,
    AnalyzeCodeImpactRequest,
    ChatRequest, ChatResponse
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """通用对话接口"""
    try:
        ai_service = get_ai_service()
        content = await ai_service.chat(request.messages, request.temperature)
        return ChatResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/analyze-requirement", response_model=AnalyzeRequirementResponse)
async def analyze_requirement(request: AnalyzeRequirementRequest):
    """分析需求，生成测试要点"""
    try:
        ai_service = get_ai_service()
        result = await ai_service.analyze_requirement(
            request.requirement_title,
            request.requirement_description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/generate-test-cases")
async def generate_test_cases(request: GenerateTestCasesRequest):
    """生成测试用例"""
    try:
        ai_service = get_ai_service()
        result = await ai_service.generate_test_cases(
            request.requirement_title,
            request.requirement_description,
            request.test_types
        )
        return {"test_cases": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/generate-test-code", response_model=GenerateTestCodeResponse)
async def generate_test_code(request: GenerateTestCodeRequest):
    """生成测试代码"""
    try:
        ai_service = get_ai_service()
        code = await ai_service.generate_test_code(
            request.test_cases,
            request.framework
        )
        return GenerateTestCodeResponse(code=code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.post("/analyze-code-impact")
async def analyze_code_impact(request: AnalyzeCodeImpactRequest):
    """分析代码变更影响"""
    try:
        ai_service = get_ai_service()
        result = await ai_service.analyze_code_impact(
            request.code_changes,
            request.requirements
        )
        return {"affected_requirements": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
