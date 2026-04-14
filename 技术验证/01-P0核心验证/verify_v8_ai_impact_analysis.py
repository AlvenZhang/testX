"""
V8验证: AI需求影响分析
验证方法: 调用AI分析新需求对现有测试代码的影响
通过标准: 成功调用AI并返回有效分析结果

运行: python verify_v8_ai_impact_analysis.py
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


def test_ai_impact_analysis():
    """AI需求影响分析测试"""
    print("=" * 50)
    print("V8 AI 需求影响分析测试")
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

    # 测试数据
    new_requirement = """
    新增需求: 用户登录功能增加短信验证码二次验证
    - 用户输入手机号后，系统发送6位数字验证码
    - 验证码有效期5分钟
    - 每个手机号每分钟只能发送1次
    - 验证码输入错误3次后账户锁定15分钟
    """

    old_requirements = [
        "用户名密码登录",
        "第三方OAuth登录(Google/GitHub)",
        "用户注册功能",
        "忘记密码重置"
    ]

    old_test_code = '''
    def test_login_with_password():
        """测试用户名密码登录"""
        response = api.post("/auth/login", {
            "username": "testuser",
            "password": "testpass"
        })
        assert response.status_code == 200
        assert "token" in response.json()

    def test_login_with_oauth():
        """测试OAuth第三方登录"""
        response = api.post("/auth/oauth/google", {
            "access_token": "google_token_xxx"
        })
        assert response.status_code == 200

    def test_register():
        """测试用户注册"""
        response = api.post("/auth/register", {
            "username": "newuser",
            "password": "password123"
        })
        assert response.status_code == 201
    '''

    code_changes = '''
    diff --git a/auth/views.py b/auth/views.py
    --- a/auth/views.py
    +++ b/auth/views.py
    @@ -10,6 +10,8 @@ def login(request):
    +    # 新增短信验证码验证逻辑
    +    if requires_sms_verification:
    +        verify_sms_code(request, code)
    '''

    # 构建提示词
    prompt = f"""你是一个测试架构师。分析新需求对现有测试的影响。

新需求：
{new_requirement}

现有需求列表：
{', '.join(old_requirements)}

现有测试代码：
{old_test_code}

代码变更：
{code_changes}

请分析并返回JSON格式的结果，包含：
1. 受影响的需求（列出受影响的现有需求及其影响等级：high/medium/low）
2. 受影响的测试代码（列出需要修改的测试函数）
3. 影响原因说明
4. 建议的测试策略

请严格按以下JSON格式返回：
{{
    "impacted_requirements": [
        {{"name": "需求名称", "level": "high/medium/low", "reason": "影响原因"}}
    ],
    "impacted_tests": [
        {{"name": "test_xxx", "reason": "需要修改的原因"}}
    ],
    "suggested_strategy": "测试策略建议"
}}
"""

    print("\n[1] 准备AI提示词...")
    print(f"    新需求: 用户登录增加短信验证码")
    print(f"    现有测试: {len(old_requirements)}个需求相关的测试")

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
                max_tokens=2000
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
        required_fields = ["impacted_requirements", "impacted_tests", "suggested_strategy"]
        for field in required_fields:
            if field not in result_json:
                print(f"    fail 缺少必需字段: {field}")
                return False

        print("\n[4] 分析结果验证:")

        impacted_reqs = result_json.get("impacted_requirements", [])
        impacted_tests = result_json.get("impacted_tests", [])

        print(f"    受影响需求数: {len(impacted_reqs)}")
        for req in impacted_reqs[:3]:
            level = req.get("level", "unknown")
            name = req.get("name", "unknown")
            print(f"      - {name}: {level}")

        print(f"    受影响测试数: {len(impacted_tests)}")
        for test in impacted_tests[:3]:
            print(f"      - {test.get('name', 'unknown')}")

        print(f"\n    建议策略: {result_json.get('suggested_strategy', 'N/A')[:100]}...")

        # 高影响需求应该被识别
        has_high_impact = any(r.get("level") == "high" for r in impacted_reqs)
        if has_high_impact:
            print("\n    ✓ AI正确识别了高影响需求")
        else:
            print("\n    ⚠ AI未识别高影响需求（可能是合理的）")

        print("\n" + "=" * 50)
        print(f"V8 测试结果: ✓ PASS")
        print("=" * 50)
        print("\n结论: AI影响分析功能正常")
        print(f"      成功识别 {len(impacted_reqs)} 个受影响需求")
        print(f"      成功识别 {len(impacted_tests)} 个受影响测试")

        return True

    except Exception as e:
        print(f"\n    fail AI调用失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = test_ai_impact_analysis()
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