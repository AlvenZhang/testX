"""
V7验证: Appium iOS自动化测试
验证方法: 启动WDA，执行简单测试
通过标准: 测试通过，截图成功

前置条件:
1. macOS机器 (必须!)
2. Xcode已安装
3. iOS设备或模拟器
4. Appium Server已安装: npm install -g appium

注意: 此测试必须在macOS上运行，Linux/Windows无法进行iOS测试

运行(仅macOS): python verify_v7_appium_ios.py
"""
import time
import sys
import os
import subprocess


def check_macOS():
    """检查是否在macOS上运行"""
    if sys.platform != "darwin":
        print("=" * 50)
        print("V7 iOS测试只能在macOS上运行")
        print("当前系统:", sys.platform)
        print("跳过此测试...")
        print("=" * 50)
        return False
    return True


def check_dependencies():
    """检查依赖工具"""
    print("\n[0] 检查依赖...")

    tools = {
        "xcrun": ["xcrun", "--version"],
        "xcodebuild": ["xcodebuild", "-version"],
    }

    for name, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"    ✓ {name}: {version_line}")
            else:
                print(f"    ✗ {name}: 未找到或配置错误")
                return False
        except Exception as e:
            print(f"    ✗ {name}: {e}")
            return False

    return True


def test_appium_ios():
    """iOS自动化测试"""
    print("=" * 50)
    print("V7 Appium iOS 自动化测试")
    print("=" * 50)

    # 1. 平台检查
    if not check_macOS():
        return None  # 跳过，不算失败

    # 2. 依赖检查
    if not check_dependencies():
        return False

    # 配置
    appium_port = int(os.getenv("APPIUM_PORT", "4723"))
    device_name = os.getenv("IOS_DEVICE_NAME", "iPhone 15 Pro")
    platform_version = os.getenv("IOS_VERSION", "17.0")
    bundle_id = os.getenv("IOS_BUNDLE_ID", "com.apple.mobilesettings")  # 设置应用

    # 尝试获取可用模拟器
    print("\n[1] 检查可用模拟器...")
    result = subprocess.run(
        ["xcrun", "simctl", "list", "devices", "available"],
        capture_output=True, text=True
    )

    simulators = []
    for line in result.stdout.split('\n'):
        if 'iPhone' in line or 'iPad' in line:
            # 提取设备名
            parts = line.strip().split('(')
            if parts:
                device = parts[0].strip()
                simulators.append(device)

    if simulators:
        print(f"    可用模拟器: {len(simulators)}")
        print(f"    示例: {simulators[0]}")
    else:
        print("    ✗ 未找到可用模拟器")
        return False

    # 3. 检查Appium服务
    print(f"\n[2] 检查Appium服务 (localhost:{appium_port})...")
    try:
        import requests
        response = requests.get(f"http://localhost:{appium_port}", timeout=2)
        print(f"    Appium服务状态: {response.status_code}")
    except:
        print("    Appium服务未运行")
        print("    请先启动Appium: appium &")
        return False

    # 4. 配置Desired Capabilities
    desired_caps = {
        "platformName": "iOS",
        "deviceName": device_name,
        "platformVersion": platform_version,
        "automationName": "XCUITest",
        "bundleId": bundle_id,
        "useNewWDA": True,
        "noReset": True,
        "newCommandTimeout": 300,
        "autoGrantPermissions": True,
    }

    print(f"\n[3] Appium配置:")
    print(f"    deviceName: {desired_caps['deviceName']}")
    print(f"    platformVersion: {desired_caps['platformVersion']}")
    print(f"    bundleId: {desired_caps['bundleId']}")

    from appium import webdriver

    driver = None
    try:
        # 5. 连接Appium
        print("\n[4] 连接Appium服务器...")
        driver = webdriver.Remote(
            f"http://localhost:{appium_port}/wd/hub",
            desired_caps
        )
        print("    ✓ 连接成功")

        # 6. 获取会话信息
        print("\n[5] 获取会话信息...")
        print(f"    sessionId: {driver.session_id}")
        print(f"    platform: {driver.platform_name}")
        print(f"    browser: {driver.browser_name}")

        # 7. 获取页面源码
        print("\n[6] 获取页面源码...")
        source = driver.page_source
        print(f"    页面大小: {len(source)} chars")
        print("    ✓ 页面源码获取成功")

        # 8. 截图
        print("\n[7] 执行截图...")
        screenshot_path = "/tmp/verify_ios_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"    ✓ 截图已保存: {screenshot_path}")

        # 9. 元素交互
        print("\n[8] 元素交互测试...")

        # 尝试找到设置中的搜索
        try:
            time.sleep(1)
            search_field = driver.find_element_by_class_name("XCUIElementTypeSearchField")
            print("    找到搜索框")
            search_field.click()
            time.sleep(1)
            print("    ✓ 点击搜索框成功")
        except Exception as e:
            print(f"    跳过搜索: {type(e).__name__}")

        # 10. 关闭键盘(如果有)
        try:
            driver.hide_keyboard()
        except:
            pass

        print("\n" + "=" * 50)
        print("V7 测试结果: ✓ PASS")
        print("=" * 50)
        print("\n结论: Appium iOS自动化测试正常")
        print("注意: iOS测试必须在macOS上运行")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            print("\n[9] 清理...")
            driver.quit()
            print("    ✓ Appium会话已关闭")


if __name__ == "__main__":
    try:
        result = test_appium_ios()
        if result is None:
            print("\nV7 测试结果: ⊘ SKIP (非macOS系统)")
            sys.exit(0)  # 跳过不算失败
        sys.exit(0 if result else 1)
    except ImportError as e:
        print(f"\n导入错误: {e}")
        print("请安装Appium: pip install appium")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
