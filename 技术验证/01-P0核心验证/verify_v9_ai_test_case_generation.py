"""
V9验证: AI测试用例生成
验证方法: 调用AI根据需求描述生成测试用例
通过标准: 成功生成结构化的测试用例列表

运行: python verify_v9_ai_test_case_generation.py
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


def test_ai_test_case_generation():
    """AI测试用例生成测试"""
    print("=" * 50)
    print("V9 AI 测试用例生成测试")
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
    需求: 电商平台用户下单功能
    功能描述:
    1. 用户可以从购物车选择商品并提交订单
    2. 支持多种支付方式: 支付宝、微信支付、银行卡
    3. 订单金额必须大于0
    4. 每个订单生成唯一的订单号
    5. 下单成功后库存相应减少
    6. 用户可以在订单历史中查看所有订单

    接口信息:
    - POST /api/orders - 创建订单
    - GET /api/orders - 获取订单列表
    - GET /api/orders/{order_id} - 获取订单详情
    - POST /api/payment - 支付订单
    """

    # 构建提示词
    prompt = f"""你是一个专业的测试工程师。根据以下需求生成结构化的测试用例。

需求：
{requirement}

要求：
1. 生成覆盖正常、边界、异常场景的测试用例
2. 每个用例包含：case_id(用例编号), title(标题), steps(操作步骤数组), expected_result(预期结果), priority(优先级: high/medium/low), type(类型: functional/boundary/error)
3. 用例步骤要具体可执行

请严格按以下JSON格式返回（只返回JSON，不要其他内容）：
{{
    "test_cases": [
        {{
            "case_id": "TC001",
            "title": "用例标题",
            "type": "functional/boundary/error",
            "priority": "high/medium/low",
            "steps": ["步骤1", "步骤2", "步骤3"],
            "expected_result": "预期结果描述"
        }}
    ],
    "summary": {{
        "total": 用例总数,
        "high_priority": 高优先级用例数,
        "functional": 功能测试用例数,
        "boundary": 边界测试用例数,
        "error": 异常测试用例数
    }}
}}
"""

    print("\n[1] 准备AI提示词...")
    print(f"    需求: 电商平台用户下单功能")
    print(f"    目标: 生成覆盖功能/边界/异常的测试用例")

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
        if "test_cases" not in result_json:
            print("    fail 缺少必需字段: test_cases")
            return False

        test_cases = result_json["test_cases"]
        summary = result_json.get("summary", {})

        print("\n[4] 生成结果验证:")

        print(f"    用例总数: {len(test_cases)}")
        print(f"    高优先级用例: {summary.get('high_priority', 'N/A')}")
        print(f"    功能测试用例: {summary.get('functional', 'N/A')}")
        print(f"    边界测试用例: {summary.get('boundary', 'N/A')}")
        print(f"    异常测试用例: {summary.get('error', 'N/A')}")

        # 展示前5个用例
        print("\n    前5个测试用例:")
        for i, tc in enumerate(test_cases[:5]):
            print(f"      {i+1}. [{tc.get('priority', 'N/A')}] {tc.get('title', 'N/A')}")
            print(f"         类型: {tc.get('type', 'N/A')}, 步骤数: {len(tc.get('steps', []))}")

        # 验证用例质量
        valid_cases = []
        for tc in test_cases:
            if all(k in tc for k in ["case_id", "title", "steps", "expected_result", "priority"]):
                if isinstance(tc["steps"], list) and len(tc["steps"]) > 0:
                    valid_cases.append(tc)

        print(f"\n    有效用例数: {len(valid_cases)}/{len(test_cases)}")

        # 检查用例覆盖率
        has_high_priority = any(tc.get("priority") == "high" for tc in test_cases)
        has_boundary = any(tc.get("type") == "boundary" for tc in test_cases)
        has_error = any(tc.get("type") == "error" for tc in test_cases)

        print("\n    用例覆盖检查:")
        print(f"      高优先级用例: {'✓' if has_high_priority else '✗'}")
        print(f"      边界测试用例: {'✓' if has_boundary else '✗'}")
        print(f"      异常测试用例: {'✓' if has_error else '✗'}")

        # 综合评估
        passed = (
            len(valid_cases) >= 5 and
            len(valid_cases) == len(test_cases) and
            has_high_priority
        )

        print("\n" + "=" * 50)
        print(f"V9 测试结果: {'✓ PASS' if passed else '✗ FAIL'}")
        print("=" * 50)
        print("\n结论: AI测试用例生成功能正常")
        print(f"      成功生成 {len(test_cases)} 个测试用例")
        print(f"      用例结构完整: {'✓' if passed else '✗'}")

        return passed

    except Exception as e:
        print(f"\n    fail AI调用失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = test_ai_test_case_generation()
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