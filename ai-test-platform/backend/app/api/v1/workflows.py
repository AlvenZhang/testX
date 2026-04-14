"""AI 自动化测试生成工作流"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ...core.database import get_db
from ...services.ai_service import get_ai_service
from ...models.requirement import Requirement
from ...models.test_case import TestCase
from ...models.test_code import TestCode
from ...schemas.ai import AnalyzeRequirementRequest, GenerateTestCasesRequest

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/generate-tests/{requirement_id}")
async def generate_tests(
    requirement_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    自动化测试生成工作流：
    1. 分析需求 → 生成测试要点
    2. 生成测试用例
    3. 生成测试代码
    4. 保存到数据库
    """
    # 获取需求
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    ai_service = get_ai_service()

    # Step 1: AI 分析需求，生成测试要点
    analysis_result = await ai_service.analyze_requirement(
        requirement.title,
        requirement.description or ""
    )

    # Step 2: AI 生成测试用例
    test_types = analysis_result.get("suggested_test_types", ["web"])
    test_cases_data = await ai_service.generate_test_cases(
        requirement.title,
        requirement.description or "",
        test_types
    )

    # Step 3: 保存测试用例到数据库
    saved_cases = []
    for i, case_data in enumerate(test_cases_data):
        case_id = f"{requirement_id[:8]}-TC-{i+1:03d}"
        test_case = TestCase(
            id=str(uuid.uuid4()),
            requirement_id=requirement_id,
            case_id=case_id,
            title=case_data.get("title", f"用例 {i+1}"),
            steps=case_data.get("steps"),
            expected_result=case_data.get("expected_result"),
            priority=case_data.get("priority", "medium"),
            status="active",
        )
        db.add(test_case)
        saved_cases.append({
            "case_id": case_id,
            "title": test_case.title,
            "steps": case_data.get("steps"),
            "expected_result": case_data.get("expected_result"),
            "priority": case_data.get("priority", "medium"),
        })

    # Step 4: AI 生成测试代码
    test_code_content = await ai_service.generate_test_code(saved_cases, "pytest")

    # Step 5: 保存测试代码
    test_code = TestCode(
        id=str(uuid.uuid4()),
        project_id=requirement.project_id,
        requirement_id=requirement_id,
        test_case_ids=[c["case_id"] for c in saved_cases],
        framework="pytest",
        code_content=test_code_content,
        version=1,
        status="active",
    )
    db.add(test_code)

    # Step 6: 更新需求状态
    requirement.status = "cases_generated"

    await db.commit()

    return {
        "requirement_id": requirement_id,
        "analysis": analysis_result,
        "test_cases": saved_cases,
        "test_code_id": test_code.id,
        "test_code_preview": test_code_content[:500] + "..." if len(test_code_content) > 500 else test_code_content,
    }


from sqlalchemy import select
