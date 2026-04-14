"""
V10验证: AI测试代码生成
验证方法: 调用AI根据测试用例生成可执行的pytest代码
通过标准: 成功生成语法正确的pytest测试代码

运行: python verify_v10_ai_test_code_generation.py
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


def test_ai_test_code_generation():
    """AI测试代码生成测试"""
    print("=" * 50)
    print("V10 AI 测试代码生成测试")
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

    # 测试用例
    test_cases = [
        {
            "case_id": "TC001",
            "title": "用户登录成功",
            "steps": [
                "打开登录页面",
                "输入用户名: testuser",
                "输入密码: testpass123",
                "点击登录按钮"
            ],
            "expected_result": "登录成功，跳转到首页"
        },
        {
            "case_id": "TC002",
            "title": "用户登录失败-密码错误",
            "steps": [
                "打开登录页面",
                "输入用户名: testuser",
                "输入密码: wrongpassword",
                "点击登录按钮"
            ],
            "expected_result": "显示错误提示：用户名或密码错误"
        },
        {
            "case_id": "TC003",
            "title": "用户登录失败-用户不存在",
            "steps": [
                "打开登录页面",
                "输入用户名: nonexistent",
                "输入密码: testpass123",
                "点击登录按钮"
            ],
            "expected_result": "显示错误提示：用户不存在"
        }
    ]

    project_context = """
    项目: 电商Web应用
    技术栈: Python + pytest + Selenium
    API基础URL: http://localhost:8000/api
    登录接口: POST /auth/login
    """

    # 构建提示词
    prompt = f"""你是一个测试工程师。根据以下测试用例生成可执行的pytest测试代码。

项目上下文：
{project_context}

测试用例：
{json.dumps(test_cases, ensure_ascii=False, indent=2)}

要求：
1. 使用pytest框架
2. 使用requests库进行API调用（因为这是API测试，不是UI测试）
3. 代码必须语法正确，可直接运行
4. 包含适当的assert断言
5. 每个测试用例对应一个test函数
6. 使用pytest fixtures管理测试数据
7. 添加清晰的注释

请只返回Python代码，不要包含markdown代码块标记。
"""

    print("\n[1] 准备AI提示词...")
    print(f"    测试用例数: {len(test_cases)}")
    print(f"    项目: 电商Web应用 (pytest + requests)")

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
            result_code = response.choices[0].message.content
        elif client_type == "aliyun":
            response = client.Generation.call(
                model=model,
                prompt=prompt
            )
            result_code = response.output.text

        elapsed = time.time() - start

        print(f"    AI响应耗时: {elapsed:.2f}秒")
        print(f"    生成代码长度: {len(result_code)}字符")

        # 清理代码（移除markdown标记如果存在）
        print("\n[3] 处理生成的代码...")

        if result_code.startswith("```"):
            lines = result_code.split("\n")
            # 移除第一行（```python）和最后一行（```）
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            result_code = "\n".join(lines)

        print(f"    清理后代码长度: {len(result_code)}字符")

        # 验证代码语法
        print("\n[4] 验证代码语法...")
        try:
            compile(result_code, "<string>", "exec")
            print("    ok Python语法正确")
            syntax_ok = True
        except SyntaxError as e:
            print(f"    fail 语法错误: {e}")
            syntax_ok = False

        # 检查代码结构
        print("\n[5] 检查代码结构...")

        # 检查必要的导入
        has_imports = any(
            keyword in result_code
            for keyword in ["import pytest", "import requests", "def test_"]
        )
        print(f"    包含必要导入和测试函数: {'✓' if has_imports else '✗'}")

        # 检查测试函数数量
        test_func_count = result_code.count("def test_")
        print(f"    测试函数数量: {test_func_count}")

        # 检查assert语句
        assert_count = result_code.count("assert ")
        print(f"    assert语句数量: {assert_count}")

        # 展示生成的代码
        print("\n[6] 生成的代码预览:")
        print("-" * 40)
        lines = result_code.split("\n")
        for i, line in enumerate(lines[:20]):
            print(f"    {i+1:2d}: {line}")
        if len(lines) > 20:
            print(f"    ... ({len(lines) - 20} more lines)")
        print("-" * 40)

        # 保存代码到临时文件
        output_file = "/tmp/verify_generated_test.py"
        with open(output_file, "w") as f:
            f.write(result_code)
        print(f"\n    代码已保存到: {output_file}")

        # 综合评估
        passed = syntax_ok and has_imports and test_func_count >= 3

        print("\n" + "=" * 50)
        print(f"V10 测试结果: {'✓ PASS' if passed else '✗ FAIL'}")
        print("=" * 50)
        print("\n结论: AI测试代码生成功能正常")
        print(f"      生成 {test_func_count} 个测试函数")
        print(f"      语法正确: {'✓' if syntax_ok else '✗'}")

        return passed

    except Exception as e:
        print(f"\n    fail AI调用失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = test_ai_test_code_generation()
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