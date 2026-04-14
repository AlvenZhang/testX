"""AI 影响分析服务"""
from typing import List, Dict
import json

from .ai_service import AIService


class ImpactService:
    """AI 影响分析服务"""

    def __init__(self):
        self.ai_service = AIService()

    async def analyze_impact(
        self,
        changed_requirement: Dict,
        all_requirements: List[Dict],
        all_test_codes: List[Dict]
    ) -> Dict:
        """
        分析需求变更对测试的影响

        Args:
            changed_requirement: 变更的需求
            all_requirements: 所有需求
            all_test_codes: 所有测试代码

        Returns:
            影响分析结果
        """
        # 构建上下文
        requirements_json = json.dumps(all_requirements, ensure_ascii=False, indent=2)
        test_codes_json = json.dumps(all_test_codes, ensure_ascii=False, indent=2)
        changed_req_json = json.dumps(changed_requirement, ensure_ascii=False, indent=2)

        prompt = f"""分析以下需求变更对现有测试的影响：

变更的需求：
{changed_req_json}

所有需求列表：
{requirements_json}

所有测试代码：
{test_codes_json}

请分析：
1. 哪些现有测试可能受到影响？
2. 需要新增哪些测试用例？
3. 需要修改哪些现有测试代码？

以 JSON 格式返回分析结果：
{{
    "affected_requirements": ["受影响的测试ID列表"],
    "new_test_cases_needed": ["建议新增的测试点"],
    "tests_to_modify": ["需要修改的测试代码ID"],
    "impact_level": "high/medium/low",
    "reason": "分析原因"
}}
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试架构师，擅长影响分析。"},
            {"role": "user", "content": prompt}
        ])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "affected_requirements": [],
                "new_test_cases_needed": [],
                "tests_to_modify": [],
                "impact_level": "unknown",
                "reason": response
            }

    async def suggest_regression_tests(
        self,
        changed_files: List[str],
        all_test_codes: List[Dict]
    ) -> List[str]:
        """
        根据变更文件建议需要执行的回归测试

        Args:
            changed_files: 变更的文件列表
            all_test_codes: 所有测试代码

        Returns:
            建议执行的测试代码ID列表
        """
        test_codes_json = json.dumps(all_test_codes, ensure_ascii=False, indent=2)
        changed_files_json = json.dumps(changed_files, ensure_ascii=False, indent=2)

        prompt = f"""根据代码变更，建议需要执行的回归测试：

变更的文件：
{changed_files_json}

所有测试代码：
{test_codes_json}

请分析哪些测试代码可能因为这些变更而需要重新执行。

以 JSON 数组格式返回需要执行的测试代码ID：
["test_code_id_1", "test_code_id_2"]
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试架构师，擅长回归测试分析。"},
            {"role": "user", "content": prompt}
        ])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []


def get_impact_service() -> ImpactService:
    """获取影响分析服务实例"""
    return ImpactService()
