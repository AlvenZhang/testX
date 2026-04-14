"""
V5验证: Android真机网络连接
验证方法: adb connect + screencap
通过标准: 截图成功

前置条件:
1. Android手机开启USB调试
2. 手机和服务器在同一网络
3. 手机开启网络ADB: adb tcpip 5555

运行: python verify_v5_android_adb.py
"""
import subprocess
import sys
import os
import time


def run_command(cmd, description=""):
    """执行shell命令并返回结果"""
    print(f"    {description}: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_android_adb_connection():
    print("=" * 50)
    print("V5 Android ADB 网络连接测试")
    print("=" * 50)

    # 配置 - 请修改为实际IP
    device_ip = os.getenv("ANDROID_DEVICE_IP", "192.168.1.100")
    device_port = int(os.getenv("ANDROID_DEVICE_PORT", "5555"))

    print(f"\n目标设备: {device_ip}:{device_port}")

    # 1. 检查adb是否安装
    print("\n[1] 检查ADB环境...")
    result = run_command(["adb", "version"], "检查adb版本")
    if result.returncode != 0:
        print("    ✗ FAIL: adb未安装或未在PATH中")
        return False
    print(f"    adb版本: {result.stdout.split()[4] if 'version' in result.stdout else 'unknown'}")

    # 2. 杀掉占用5555端口的进程(可选)
    print("\n[2] 清理端口...")
    run_command(["adb", "kill-server"], "停止adb服务")
    time.sleep(1)
    run_command(["adb", "start-server"], "启动adb服务")
    time.sleep(1)

    # 3. 连接设备
    print("\n[3] 连接设备...")
    result = run_command(
        ["adb", "connect", f"{device_ip}:{device_port}"],
        "执行adb connect"
    )
    print(f"    输出: {result.stdout.strip()}")
    print(f"    错误: {result.stderr.strip()}")

    if "connected" in result.stdout or "already connected" in result.stdout:
        print("    ✓ 连接成功")
    else:
        print("    ✗ 连接失败")
        print("\n    故障排查:")
        print("    1. 确认手机已开启USB调试")
        print("    2. 确认手机和服务器在同一网络")
        print("    3. 确认手机已开启网络ADB (adb tcpip 5555)")
        print("    4. 检查防火墙是否阻止5555端口")
        return False

    # 4. 获取设备状态
    print("\n[4] 获取设备状态...")
    result = run_command(
        ["adb", "-s", f"{device_ip}:{device_port}", "get-state"],
        "获取设备状态"
    )
    state = result.stdout.strip()
    print(f"    设备状态: {state}")

    if state != "device":
        print(f"    ✗ 设备状态异常: {state}")
        return False
    print("    ✓ 设备状态正常")

    # 5. 获取设备信息
    print("\n[5] 获取设备信息...")
    result = run_command(
        ["adb", "-s", f"{device_ip}:{device_port}", "shell", "getprop", "ro.product.model"],
        "获取设备型号"
    )
    model = result.stdout.strip()
    print(f"    设备型号: {model}")

    result = run_command(
        ["adb", "-s", f"{device_ip}:{device_port}", "shell", "getprop", "ro.build.version.release"],
        "获取Android版本"
    )
    version = result.stdout.strip()
    print(f"    Android版本: {version}")

    # 6. 截图测试
    print("\n[6] 执行截图测试...")
    result = run_command(
        ["adb", "-s", f"{device_ip}:{device_port}", "exec-out", "screencap", "-p"],
        "截图"
    )

    if len(result.stdout) > 1000:
        # 保存截图
        screenshot_path = "/tmp/verify_android_screenshot.png"
        with open(screenshot_path, "wb") as f:
            f.write(result.stdout)
        print(f"    ✓ 截图成功")
        print(f"    截图大小: {len(result.stdout)} bytes")
        print(f"    截图路径: {screenshot_path}")
    else:
        print(f"    ✗ 截图失败或图片过小")
        return False

    # 7. 读取本地截图(验证exec-out可用)
    print("\n[7] 验证截图可读性...")
    if os.path.exists(screenshot_path):
        size = os.path.getsize(screenshot_path)
        print(f"    ✓ 截图文件有效")
        print(f"    文件大小: {size} bytes")
    else:
        print(f"    ✗ 截图文件不存在")
        return False

    # 8. 设备断开测试
    print("\n[8] 断开连接测试...")
    result = run_command(
        ["adb", "-s", f"{device_ip}:{device_port}", "disconnect"],
        "断开连接"
    )
    print(f"    输出: {result.stdout.strip()}")

    print("\n" + "=" * 50)
    print("V5 测试结果: ✓ PASS")
    print("=" * 50)
    print("\n结论: Android真机可以通过网络ADB连接")
    print("后续Appium可以基于此连接进行自动化测试")

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
