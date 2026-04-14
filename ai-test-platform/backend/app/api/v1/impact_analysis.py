"""AI 影响分析 API"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.requirement import Requirement
from ...models.test_code import TestCode
from ...services.impact_service import get_impact_service

router = APIRouter(prefix="/impact-analysis", tags=["impact-analysis"])


@router.post("/requirement/{requirement_id}")
async def analyze_requirement_impact(
    requirement_id: str,
    db: AsyncSession = Depends(get_db),
):
    """分析需求变更的影响"""
    # 获取变更的需求
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    changed_requirement = result.scalar_one_or_none()
    if not changed_requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 获取项目的所有需求
    result = await db.execute(select(Requirement).where(Requirement.project_id == changed_requirement.project_id))
    all_requirements = result.scalars().all()

    # 获取项目的所有测试代码
    result = await db.execute(select(TestCode).where(TestCode.project_id == changed_requirement.project_id))
    all_test_codes = result.scalars().all()

    # 转换为字典
    changed_req_dict = {
        "id": changed_requirement.id,
        "title": changed_requirement.title,
        "description": changed_requirement.description,
        "status": changed_requirement.status,
    }

    all_reqs_list = [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "status": r.status,
        }
        for r in all_requirements
    ]

    all_codes_list = [
        {
            "id": c.id,
            "framework": c.framework,
            "code_content": c.code_content[:200] + "...",  # 只取前200字符
        }
        for c in all_test_codes
    ]

    # 调用影响分析服务
    impact_service = get_impact_service()
    result = await impact_service.analyze_impact(
        changed_req_dict,
        all_reqs_list,
        all_codes_list
    )

    return {
        "requirement_id": requirement_id,
        "analysis": result
    }


@router.post("/regression-suggest")
async def suggest_regression_tests(
    changed_files: List[str],
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """根据代码变更建议回归测试"""
    # 获取项目的所有测试代码
    result = await db.execute(select(TestCode).where(TestCode.project_id == project_id))
    all_test_codes = result.scalars().all()

    all_codes_list = [
        {
            "id": c.id,
            "framework": c.framework,
            "code_content": c.code_content[:200] + "...",
        }
        for c in all_test_codes
    ]

    impact_service = get_impact_service()
    suggested_tests = await impact_service.suggest_regression_tests(
        changed_files,
        all_codes_list
    )

    return {
        "project_id": project_id,
        "changed_files": changed_files,
        "suggested_test_codes": suggested_tests
    }
