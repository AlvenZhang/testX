"""AI 自动化测试生成工作流"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import json
import asyncio
import logging

from ...core.database import get_db
from ...services.ai_service import get_ai_service
from ...services.impact_service import get_impact_service
from ...models.requirement import Requirement
from ...models.test_case import TestCase
from ...models.test_code import TestCode
from ...schemas.ai import AnalyzeRequirementRequest, GenerateTestCasesRequest

router = APIRouter(prefix="/workflows", tags=["workflows"])
logger = logging.getLogger(__name__)


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



@router.post("/generate-tests-stream/{requirement_id}")
async def generate_tests_stream(
    requirement_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    流式测试生成工作流 - 通过 SSE 流式返回生成进度
    """
    async def event_generator():
        logger.info(f"Starting streaming test generation for requirement: {requirement_id}")
        try:
            # 获取需求
            result = await db.execute(
                select(Requirement).where(Requirement.id == requirement_id)
            )
            requirement = result.scalar_one_or_none()
            if not requirement:
                logger.error(f"Requirement not found: {requirement_id}")
                yield f"data: {json.dumps({'type': 'error', 'content': 'Requirement not found'})}\n\n"
                return

            ai_service = get_ai_service()
            logger.info(f"Processing requirement: {requirement.title}")

            # Step 1: 分析需求
            logger.info("Step 1: Analyzing requirement")
            yield f"data: {json.dumps({'type': 'progress', 'content': '📋 Step 1/4: 正在分析需求...'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'content': '   ├─ 获取需求信息: {requirement.title}'})}\n\n"
            analysis_result = await ai_service.analyze_requirement(
                requirement.title,
                requirement.description or ""
            )
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   ├─ 解析测试要点: {len(analysis_result.get("test_points", []))} 项'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   └─ 识别风险点: {len(analysis_result.get("risk_points", []))} 项'})}\n\n"
            logger.info(f"Requirement analysis complete: {len(analysis_result.get('test_points', []))} test points")
            yield f"data: {json.dumps({'type': 'analysis', 'content': json.dumps(analysis_result, ensure_ascii=False)})}\n\n"

            # Step 2: 生成测试用例
            logger.info("Step 2: Generating test cases")
            yield f"data: {json.dumps({'type': 'progress', 'content': '📝 Step 2/4: 正在生成测试用例...'})}\n\n"
            test_types = analysis_result.get("suggested_test_types", ["web"])
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   ├─ 测试类型: {", ".join(test_types)}'})}\n\n"

            # 流式生成测试用例
            cases_prompt = f"""为以下需求生成测试用例：

需求标题：{requirement.title}
需求描述：{requirement.description or ""}
测试类型：{', '.join(test_types)}

【重要】你必须返回严格的JSON数组格式，每个元素包含以下字段：
- title: string，用例标题，必填
- steps: string，测试步骤，必填
- expected_result: string，预期结果，必填
- priority: string，优先级，只能是 "low" | "medium" | "high" 之一

示例格式：
[
  {{"title": "登录成功-正确账号密码", "steps": "1. 打开APP\\n2. 输入正确账号\\n3. 输入正确密码\\n4. 点击登录", "expected_result": "登录成功，跳转到首页", "priority": "high"}},
  {{"title": "登录失败-错误密码", "steps": "1. 打开APP\\n2. 输入正确账号\\n3. 输入错误密码\\n4. 点击登录", "expected_result": "提示密码错误", "priority": "high"}}
]

只返回上述JSON数组，不要包含任何其他文字或解释。"""

            full_response = ""
            async for chunk in ai_service.chat_stream([
                {"role": "system", "content": "你是一个专业的测试工程师。你的任务是根据需求生成测试用例。必须严格返回JSON数组格式，不要包含任何其他文字。"},
                {"role": "user", "content": cases_prompt}
            ]):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # 解析测试用例
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   ├─ AI 正在生成用例内容...'})}\n\n"
            try:
                test_cases_data = json.loads(full_response)
                # 验证是数组
                if not isinstance(test_cases_data, list):
                    logger.warning(f"AI returned non-array: {type(test_cases_data)}")
                    test_cases_data = []
                logger.info(f"Parsed {len(test_cases_data)} test cases from AI response")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse test cases JSON: {e}, response: {full_response[:500]}")
                test_cases_data = []

            # 保存测试用例
            saved_cases = []
            valid_priorities = {"low", "medium", "high"}
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   ├─ 保存 {len(test_cases_data)} 个测试用例到数据库...'})}\n\n"
            for i, case_data in enumerate(test_cases_data):
                # 验证数据类型
                if not isinstance(case_data, dict):
                    logger.warning(f"Skipping invalid case data (not a dict): {case_data}")
                    continue

                # 提取并验证字段
                title = case_data.get("title", f"用例 {i+1}")
                steps = case_data.get("steps", "")
                expected_result = case_data.get("expected_result", "")
                priority = case_data.get("priority", "medium")

                # 确保是字符串
                if not isinstance(title, str):
                    title = str(title) if title else f"用例 {i+1}"
                if not isinstance(steps, str):
                    steps = str(steps) if steps else ""
                if not isinstance(expected_result, str):
                    expected_result = str(expected_result) if expected_result else ""
                if not isinstance(priority, str) or priority not in valid_priorities:
                    priority = "medium"

                case_id = f"{requirement_id[:8]}-TC-{i+1:03d}"
                test_case = TestCase(
                    id=str(uuid.uuid4()),
                    requirement_id=requirement_id,
                    case_id=case_id,
                    title=title,
                    steps=steps,
                    expected_result=expected_result,
                    priority=priority,
                    status="active",
                )
                db.add(test_case)
                saved_cases.append({
                    "case_id": case_id,
                    "title": title,
                    "steps": steps,
                    "expected_result": expected_result,
                    "priority": priority,
                })
                yield f"data: {json.dumps({'type': 'progress', 'content': f'   │  ├─ [{case_id}] {title}'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   └─ 完成! 共保存 {len(saved_cases)} 个用例'})}\n\n"
            logger.info(f"Saved {len(saved_cases)} test cases to database")

            yield f"data: {json.dumps({'type': 'test_cases', 'content': json.dumps(saved_cases, ensure_ascii=False)})}\n\n"

            # Step 3: 生成测试代码
            logger.info("Step 3: Generating test code")
            yield f"data: {json.dumps({'type': 'progress', 'content': '💻 Step 3/4: 正在生成测试代码...'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   ├─ 生成 pytest 代码 ({len(saved_cases)} 个用例)'})}\n\n"
            test_code_content = await ai_service.generate_test_code(saved_cases, "pytest")

            # 流式返回代码
            async for chunk in ai_service.chat_stream([
                {"role": "system", "content": "你是一个专业的测试开发工程师。"},
                {"role": "user", "content": f"根据以下测试用例生成pytest测试代码：\n{json.dumps(saved_cases, ensure_ascii=False)}\n\n只返回代码，不要其他解释。"}
            ]):
                yield f"data: {json.dumps({'type': 'code_chunk', 'content': chunk})}\n\n"

            # 保存测试代码
            yield f"data: {json.dumps({'type': 'progress', 'content': f'   └─ 保存测试代码到数据库...'})}\n\n"
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
            logger.info(f"Saved test code: {test_code.id}")

            # 更新需求状态
            requirement.status = "cases_generated"
            await db.commit()
            logger.info(f"Requirement {requirement_id} status updated to 'cases_generated'")

            yield f"data: {json.dumps({'type': 'progress', 'content': '✅ Step 4/4: 完成! 更新需求状态为"用例已生成"'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'test_code_id': test_code.id, 'requirement_id': requirement_id})}\n\n"

        except Exception as e:
            logger.error(f"Streaming generation error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
