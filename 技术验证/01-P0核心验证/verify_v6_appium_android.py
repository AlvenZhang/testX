"""
V6验证: Appium Android自动化测试
验证方法: 启动Appium，连接设备，执行简单测试
通过标准: 测试通过，截图成功

前置条件:
1. Appium Server 2.x 已安装并启动 (npm install -g appium)
2. V5验证已通过(adb连接正常)
3. Android设备已通过网络连接

运行: python verify_v6_appium_android.py
"""
import time
import sys
import os
import subprocess
from appium import webdriver
from appium.webdriver.extensions.android.nativekey import AndroidKey


def check_appium_server(port=4723):
    """检查Appium服务是否运行"""
    print(f"\n[0] 检查Appium服务 (localhost:{port})...")

    try:
        import requests
        response = requests.get(f"http://localhost:{port}", timeout=2)
        print(f"    Appium服务状态: {response.status_code}")
        return True
    except:
        pass

    # 检查进程
    result = subprocess.run(["pgrep", "-f", "appium"], capture_output=True)
    if result.returncode == 0:
        print("    Appium进程运行中，但HTTP服务未响应")
        return True

    print("    ✗ Appium服务未运行")
    print("    请先启动Appium: appium &")
    return False


def test_appium_android():
    print("=" * 50)
    print("V6 Appium Android 自动化测试")
    print("=" * 50)

    # 配置
    device_ip = os.getenv("ANDROID_DEVICE_IP", "192.168.1.100")
    device_port = int(os.getenv("ANDROID_DEVICE_PORT", "5555"))
    appium_port = int(os.getenv("APPIUM_PORT", "4723"))

    # 1. 检查Appium服务
    if not check_appium_server(appium_port):
        return False

    # 2. 配置Desired Capabilities
    desired_caps = {
        "platformName": "Android",
        "deviceName": f"AndroidDevice_{device_ip}",
        "udid": f"{device_ip}:{device_port}",
        "automationName": "UiAutomator2",
        "noReset": True,
        "newCommandTimeout": 300,
        "skipUnlock": True,
        # 性能优化
        "androidInstallTimeout": 120000,
        "autoGrantPermissions": True,
    }

    print(f"\n[1] Appium配置:")
    print(f"    设备: {device_ip}:{device_port}")
    print(f"    Appium: localhost:{appium_port}")
    print(f"    automationName: {desired_caps['automationName']}")

    driver = None
    try:
        # 3. 连接Appium
        print("\n[2] 连接Appium服务器...")
        driver = webdriver.Remote(
            f"http://localhost:{appium_port}/wd/hub",
            desired_caps
        )
        print("    ✓ 连接成功")

        # 4. 获取设备信息
        print("\n[3] 获取设备信息...")
        print(f"    sessionId: {driver.session_id}")
        print(f"    platform: {driver.platform_name}")
        print(f"    platformVersion: {driver.platform_version}")
        print(f"    deviceName: {driver.device_name}")

        # 5. 启动设置应用
        print("\n[4] 启动设置应用...")
        driver.start_activity("com.android.settings", ".Settings")
        time.sleep(2)
        print("    ✓ 设置应用已启动")

        # 6. 获取页面源码
        print("\n[5] 获取页面源码...")
        source = driver.page_source
        print(f"    页面大小: {len(source)} chars")
        print("    ✓ 页面源码获取成功")

        # 7. 截图
        print("\n[6] 执行截图...")
        screenshot_path = "/tmp/verify_appium_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"    ✓ 截图已保存: {screenshot_path}")

        # 8. 查找并点击元素
        print("\n[7] 元素交互测试...")

        # 尝试找到搜索按钮
        try:
            search_btn = driver.find_element_by_accessibility_id("Search")
            print("    找到搜索按钮")
            search_btn.click()
            time.sleep(1)
            print("    ✓ 点击搜索按钮成功")
        except Exception as e:
            print(f"    跳过搜索按钮(未找到): {type(e).__name__}")

        # 尝试点击某个列表项
        try:
            # 等待一下让页面加载
            time.sleep(1)
            # 在设置中查找WiFi设置
            wifi = driver.find_element_by_xpath("//*[contains(@text, 'Wi-Fi') or contains(@text, 'WLAN')]")
            print("    找到WiFi设置项")
            wifi.click()
            time.sleep(1)
            print("    ✓ 点击WiFi成功")
        except Exception as e:
            print(f"    跳过WiFi点击: {type(e).__name__}")

        # 9. 再次截图
        print("\n[8] 交互后截图...")
        driver.save_screenshot("/tmp/verify_appium_interaction.png")
        print("    ✓ 交互后截图已保存")

        # 10. 获取当前Activity
        print("\n[9] 获取当前Activity...")
        current_activity = driver.current_activity
        print(f"    current_activity: {current_activity}")

        print("\n" + "=" * 50)
        print("V6 测试结果: ✓ PASS")
        print("=" * 50)
        print("\n结论: Appium Android自动化测试正常")
        print("后续可以基于此进行UI自动化测试")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            print("\n[10] 清理...")
            driver.quit()
            print("    ✓ Appium会话已关闭")


if __name__ == "__main__":
    try:
        result = test_appium_android()
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
