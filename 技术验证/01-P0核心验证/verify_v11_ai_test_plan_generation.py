"""
V11验证: AI测试方案生成
验证方法: 调用AI根据需求生成完整的测试方案
通过标准: 成功生成包含测试范围、策略、风险的测试方案

运行: python verify_v11_ai_test_plan_generation.py
"""
import os
import sys
import json

# AI模型配置
AI_CONFIG = {
    "model": os.getenv("AI_MODEL_NAME", "doubao-seed-2.0-code"),
    "api_key": os.getenv("VOLCENGINE_API_KEY", ""),
    "openai_key": os.getenv("OPENAI_API_KEY", ""),
    "aliyun_key": os.getenv("ALIYUN_API_KEY", ""),
    "deepseek_key": os.getenv("DEEPSEEK_API_KEY", ""),
    "base_url": os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3")
}


def get_ai_client():
    """获取AI客户端"""
    if AI_CONFIG["api_key"]:
        return "volcengine"
    elif AI_CONFIG["deepseek_key"]:
        return "deepseek"
    elif AI_CONFIG["openai_key"]:
        return "openai"
    elif AI_CONFIG["aliyun_key"]:
        return "aliyun"
    return None


def test_ai_test_plan_generation():
    """AI测试方案生成测试"""
    print("=" * 50)
    print("V11 AI 测试方案生成测试")
    print("=" * 50)

    client_type = get_ai_client()
    if not client_type:
        print("\n[0] 检查AI API密钥...")
        print("    fail 未找到有效的AI API密钥")
        print("    请设置以下环境变量之一:")
        print("    - VOLCENGINE_API_KEY (豆包/火山引擎)")
        print("    - DEEPSEEK_API_KEY")
        print("    - OPENAI_API_KEY")
        print("    - ALIYUN_API_KEY")
        return False

    print(f"\n[0] AI配置:")
    print(f"    可用客户端: {client_type}")
    print(f"    模型: {AI_CONFIG['model']}")

    # 测试需求
    requirement = """
    需求名称: 电商平台支付功能优化
    需求描述:
    1. 新增花呗分期支付功能
    2. 新增信用卡支付功能
    3. 优化支付失败时的用户体验，显示具体失败原因
    4. 支付完成后发送短信通知用户
    5. 支持支付密码记忆功能（免密支付开关）

    技术实现:
    - 后端: Python FastAPI + MySQL
    - 前端: React 18 + Ant Design
    - 支付网关: 支付宝、微信支付
    - 消息队列: Redis Stream

    业务规则:
    - 花呗分期仅支持3/6/12期
    - 信用卡支付限额单笔10000元
    - 免密支付单笔限额500元
    - 支付超时时间30分钟
    """

    # 构建提示词
    prompt = f"""你是一个测试架构师。根据以下需求生成完整的测试方案。

需求：
{requirement}

请生成包含以下内容的测试方案：

1. 测试范围（Scope）
   - 功能测试范围
   - 需要重点测试的场景

2. 测试类型（Test Types）
   - 列出需要执行的测试类型（功能测试、接口测试、性能测试、安全测试等）

3. 测试策略（Test Strategy）
   - 如何执行上述测试类型
   - 测试环境和数据要求
   - 测试执行顺序

4. 风险点分析（Risk Points）
   - 可能存在的测试风险
   - 风险等级（high/medium/low）
   - 风险应对措施

请严格按以下JSON格式返回：
{{
    "test_scope": {{
        "functional": ["功能点1", "功能点2"],
        "focus_areas": ["重点测试区域1", "重点测试区域2"]
    }},
    "test_types": [
        {{"type": "功能测试", "description": "描述", "priority": "high/medium/low"}},
        {{"type": "接口测试", "description": "描述", "priority": "high/medium/low"}},
        {{"type": "性能测试", "description": "描述", "priority": "high/medium/low"}},
        {{"type": "安全测试", "description": "描述", "priority": "high/medium/low"}}
    ],
    "test_strategy": {{
        "environment": "测试环境要求",
        "test_data": "测试数据要求",
        "execution_order": ["步骤1", "步骤2"],
        "automation_scope": "可自动化测试的范围"
    }},
    "risk_points": [
        {{"risk": "风险描述", "level": "high/medium/low", "mitigation": "应对措施"}}
    ],
    "summary": "测试方案总结"
}}
"""

    print("\n[1] 准备AI提示词...")
    print(f"    需求: 电商平台支付功能优化")
    print(f"    目标: 生成完整测试方案")

    print("\n[2] 调用AI服务...")
    try:
        if client_type == "volcengine":
            import openai
            client = openai.OpenAI(
                api_key=AI_CONFIG["api_key"],
                base_url=AI_CONFIG["base_url"]
            )
            model = AI_CONFIG["model"]
        elif client_type == "deepseek":
            import openai
            client = openai.OpenAI(
                api_key=AI_CONFIG["deepseek_key"],
                base_url="https://api.deepseek.com"
            )
            model = "deepseek-chat"
        elif client_type == "openai":
            import openai
            client = openai.OpenAI(api_key=AI_CONFIG["openai_key"])
            model = "gpt-4o"
        elif client_type == "aliyun":
            import dashscope
            client = dashscope
            model = AI_CONFIG["model"]
            dashscope.api_key = AI_CONFIG["aliyun_key"]

        print(f"    使用模型: {model}")

        import time
        start = time.time()

        if client_type == "volcengine" or client_type == "deepseek" or client_type == "openai":
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=3000
            )
            result_text = response.choices[0].message.content
        elif client_type == "aliyun":
            response = client.Generation.call(
                model=model,
                prompt=prompt
            )
            result_text = response.output.text

        elapsed = time.time() - start

        print(f"    AI响应耗时: {elapsed:.2f}秒")
        print(f"    原始响应长度: {len(result_text)}字符")

        # 解析JSON结果
        print("\n[3] 解析AI响应...")

        # 尝试提取JSON
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            result_json = json.loads(result_text[json_start:json_end])
        else:
            print("    fail 无法解析AI响应为JSON格式")
            print(f"    响应内容: {result_text[:500]}...")
            return False

        print("    ok 成功解析JSON")

        # 验证结果结构
        required_fields = ["test_scope", "test_types", "test_strategy", "risk_points"]
        for field in required_fields:
            if field not in result_json:
                print(f"    fail 缺少必需字段: {field}")
                return False

        print("\n[4] 测试方案内容验证:")

        # 测试范围
        scope = result_json.get("test_scope", {})
        functional = scope.get("functional", [])
        focus_areas = scope.get("focus_areas", [])
        print(f"\n    测试范围:")
        print(f"      功能点数量: {len(functional)}")
        for f in functional[:3]:
            print(f"        - {f}")
        print(f"      重点区域数量: {len(focus_areas)}")

        # 测试类型
        test_types = result_json.get("test_types", [])
        print(f"\n    测试类型: {len(test_types)}种")
        for tt in test_types:
            priority = tt.get("priority", "N/A")
            ttype = tt.get("type", "N/A")
            print(f"        [{priority}] {ttype}")

        # 测试策略
        strategy = result_json.get("test_strategy", {})
        execution_order = strategy.get("execution_order", [])
        print(f"\n    测试策略:")
        print(f"      执行步骤数: {len(execution_order)}")
        for step in execution_order[:3]:
            print(f"        - {step}")

        # 风险点
        risk_points = result_json.get("risk_points", [])
        print(f"\n    风险点: {len(risk_points)}个")
        high_risks = [r for r in risk_points if r.get("level") == "high"]
        print(f"      高风险: {len(high_risks)}个")
        for r in risk_points[:3]:
            print(f"        [{r.get('level', 'N/A')}] {r.get('risk', 'N/A')[:50]}...")

        # 总结
        summary = result_json.get("summary", "")
        print(f"\n    方案总结:")
        print(f"      {summary[:100]}...")

        # 验证完整性
        has_high_priority_tests = any(
            tt.get("priority") == "high" for tt in test_types
        )
        has_high_risks = any(r.get("level") == "high" for r in risk_points)

        print("\n    完整性检查:")
        print(f"      有高优先级测试: {'✓' if has_high_priority_tests else '✗'}")
        print(f"      有高风险识别: {'✓' if has_high_risks else '✗'}")

        # 综合评估
        passed = (
            len(functional) >= 3 and
            len(test_types) >= 3 and
            len(execution_order) >= 2 and
            len(risk_points) >= 2
        )

        print("\n" + "=" * 50)
        print(f"V11 测试结果: {'✓ PASS' if passed else '✗ FAIL'}")
        print("=" * 50)
        print("\n结论: AI测试方案生成功能正常")
        print(f"      覆盖 {len(functional)} 个功能点")
        print(f"      识别 {len(test_types)} 种测试类型")
        print(f"      识别 {len(risk_points)} 个风险点")

        return passed

    except Exception as e:
        print(f"\n    fail AI调用失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = test_ai_test_plan_generation()
        sys.exit(0 if result else 1)
    except ImportError as e:
        print(f"\n导入错误: {e}")
        print("请安装AI依赖: pip install openai dashscope")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)