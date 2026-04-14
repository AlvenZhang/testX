"""
V6验证: Appium Android自动化测试
验证方法: Appium连接设备，执行简单测试
通过标准: 连接成功，截图成功

运行: python verify_v6_appium_android.py
"""
import time
import sys
import os
import subprocess

def test_appium_android():
    print("=" * 50)
    print("V6 Appium Android 自动化测试")
    print("=" * 50)

    # 检查USB设备
    print("\n[1] 检查USB设备...")
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")[1:]

    usb_device = None
    for line in lines:
        if line.strip() and "device" in line:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1] == "device":
                usb_device = parts[0]
                print(f"    找到USB设备: {usb_device}")
                break

    if not usb_device:
        print("    未找到USB设备")
        return False

    # 检查Appium
    print("\n[2] 检查Appium服务...")
    try:
        import requests
        response = requests.get("http://localhost:4723", timeout=2)
        print(f"    Appium服务状态: {response.status_code}")
    except:
        print("    Appium服务未运行")
        print("    请先启动Appium: appium &")
        return False

    # Appium 2.x
    from appium import webdriver
    from appium.options.android import UiAutomator2Options

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = f"AndroidDevice_{usb_device}"
    options.udid = usb_device
    options.automation_name = "UiAutomator2"
    options.no_reset = True
    options.new_command_timeout = 60
    options.auto_grant_permissions = True

    print("\n[3] 连接Appium...")
    try:
        driver = webdriver.Remote("http://localhost:4723", options=options)
        print("    ok 连接成功")
    except Exception as e:
        print(f"    fail 连接失败: {e}")
        return False

    try:
        print("\n[4] 截图测试...")
        driver.save_screenshot("/tmp/verify_android_appium.png")
        print("    ok 截图成功")

        print("\n[5] 关闭Appium会话")
        driver.quit()
        print("    ok 会话已关闭")

        print("\n" + "=" * 50)
        print("V6 测试结果: PASS")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"    fail 测试失败: {e}")
        try:
            driver.quit()
        except:
            pass
        return False


if __name__ == "__main__":
    try:
        result = test_appium_android()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
