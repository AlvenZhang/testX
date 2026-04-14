"""AI 自动化测试生成工作流"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ...core.database import get_db
from ...services.ai_service import get_ai_service
from ...services.impact_service import get_impact_service
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


@router.post("/analyze-impact/{requirement_id}")
async def analyze_impact(
    requirement_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    分析需求变更的影响
    1. 获取变更的需求
    2. 获取所有相关需求和测试代码
    3. AI 分析影响范围
    """
    # 获取变更的需求
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 获取所有需求
    all_reqs_result = await db.execute(
        select(Requirement).where(Requirement.project_id == requirement.project_id)
    )
    all_requirements = [
        {"id": r.id, "title": r.title, "description": r.description}
        for r in all_reqs_result.scalars().all()
    ]

    # 获取所有测试代码
    all_codes_result = await db.execute(
        select(TestCode).where(TestCode.project_id == requirement.project_id)
    )
    all_test_codes = [
        {"id": c.id, "requirement_id": c.requirement_id, "code_content": c.code_content[:200]}
        for c in all_codes_result.scalars().all()
    ]

    # AI 分析影响
    impact_service = get_impact_service()
    impact_result = await impact_service.analyze_impact(
        {"id": requirement.id, "title": requirement.title, "description": requirement.description},
        all_requirements,
        all_test_codes
    )

    return {
        "requirement_id": requirement_id,
        "impact_analysis": impact_result,
    }

