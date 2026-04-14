"""
V5验证: Android真机USB连接
验证方法: adb devices + screencap via USB
通过标准: 截图成功

前置条件:
1. Android手机开启USB调试
2. 通过USB连接到电脑

运行: python verify_v5_android_adb.py
"""
import subprocess
import sys
import os
import time


def run_command(cmd, description="", binary=False):
    """执行shell命令并返回结果"""
    print(f"    {description}: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True)
    if binary:
        return result
    result.stdout = result.stdout.decode('utf-8', errors='replace')
    result.stderr = result.stderr.decode('utf-8', errors='replace')
    return result


def test_android_adb_connection():
    print("=" * 50)
    print("V5 Android ADB USB连接测试")
    print("=" * 50)

    # 1. 检查USB设备
    print("\n[1] 检查USB连接的设备...")
    result = run_command(["adb", "devices"], "列出设备")
    lines = result.stdout.strip().split("\n")[1:]

    usb_device = None
    for line in lines:
        if line.strip() and "device" in line:
            parts = line.split("\t")
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]
                if status == "device":
                    usb_device = serial
                    print(f"    找到USB设备: {serial}")
                    break

    if not usb_device:
        print("    未找到USB设备")
        print("\n故障排查:")
        print("1. 确认手机已开启USB调试")
        print("2. 确认USB线连接正常")
        print("3. 在手机上确认'允许USB调试'弹窗")
        return False

    # 2. 检查adb版本
    print("\n[2] 检查ADB环境...")
    result = run_command(["adb", "version"], "检查adb版本")
    if result.returncode != 0:
        print("    FAIL: adb未安装或未在PATH中")
        return False
    version_line = result.stdout.split('\n')[0]
    print(f"    {version_line}")

    # 3. 获取设备信息
    print("\n[3] 获取设备信息...")
    result = run_command(
        ["adb", "-s", usb_device, "shell", "getprop", "ro.product.model"],
        "获取设备型号"
    )
    model = result.stdout.strip()
    print(f"    设备型号: {model}")

    result = run_command(
        ["adb", "-s", usb_device, "shell", "getprop", "ro.build.version.release"],
        "获取Android版本"
    )
    version = result.stdout.strip()
    print(f"    Android版本: {version}")

    # 4. 获取设备状态
    print("\n[4] 获取设备状态...")
    result = run_command(
        ["adb", "-s", usb_device, "get-state"],
        "获取设备状态"
    )
    state = result.stdout.strip()
    print(f"    设备状态: {state}")
    if state != "device":
        print(f"    FAIL: 设备状态异常")
        return False
    print("    PASS: 设备状态正常")

    # 5. USB截图测试
    print("\n[5] 执行USB截图测试...")
    result = run_command(
        ["adb", "-s", usb_device, "exec-out", "screencap", "-p"],
        "截图",
        binary=True
    )

    if len(result.stdout) > 1000:
        screenshot_path = "/tmp/verify_android_usb_screenshot.png"
        with open(screenshot_path, "wb") as f:
            f.write(result.stdout)
        print(f"    PASS: USB截图成功")
        print(f"    截图大小: {len(result.stdout)} bytes")
        print(f"    截图路径: {screenshot_path}")
    else:
        print(f"    FAIL: USB截图失败或图片过小")
        return False

    # 6. 验证截图文件
    print("\n[6] 验证截图文件...")
    if os.path.exists(screenshot_path):
        size = os.path.getsize(screenshot_path)
        print(f"    PASS: 截图文件有效")
        print(f"    文件大小: {size} bytes")
    else:
        print(f"    FAIL: 截图文件不存在")
        return False

    print("\n" + "=" * 50)
    print("V5 测试结果: PASS")
    print("=" * 50)
    print("\n结论: Android真机USB连接正常")
    print("可通过USB进行Appium自动化测试")

    return True


if __name__ == "__main__":
    try:
        result = test_android_adb_connection()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
