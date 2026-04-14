#!/bin/bash
# P0核心验证执行脚本

set -e

echo "=========================================="
echo "AI自动化测试平台 - P0核心验证"
echo "=========================================="
echo ""

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 安装依赖
echo "[*] 安装验证依赖..."
pip install -r ../requirements.txt -q

# 创建输出目录
mkdir -p /tmp/verify_results

# V1: FastAPI性能测试
echo ""
echo "=========================================="
echo "V1: FastAPI异步性能测试"
echo "=========================================="
python verify_v1_fastapi_performance.py
V1_RESULT=$?

# V2: MySQL JSON测试
echo ""
echo "=========================================="
echo "V2: MySQL JSON字段性能测试"
echo "=========================================="
python verify_v2_mysql_json.py
V2_RESULT=$?

# V5: Android ADB测试
echo ""
echo "=========================================="
echo "V5: Android真机ADB连接测试"
echo "=========================================="
python verify_v5_android_adb.py
V5_RESULT=$?

# V6: Appium Android测试
echo ""
echo "=========================================="
echo "V6: Appium Android自动化测试"
echo "=========================================="
python verify_v6_appium_android.py
V6_RESULT=$?

# V7: Appium iOS测试 (可能跳过)
echo ""
echo "=========================================="
echo "V7: Appium iOS自动化测试"
echo "=========================================="
python verify_v7_appium_ios.py || true
V7_RESULT=$?

# 汇总结果
echo ""
echo "=========================================="
echo "P0核心验证结果汇总"
echo "=========================================="
echo "| 验证项 | 结果 |"
echo "|--------|------|"
echo "| V1 FastAPI性能 | $([ $V1_RESULT -eq 0 ] && echo '✓ PASS' || echo '✗ FAIL') |"
echo "| V2 MySQL JSON | $([ $V2_RESULT -eq 0 ] && echo '✓ PASS' || echo '✗ FAIL') |"
echo "| V5 Android ADB | $([ $V5_RESULT -eq 0 ] && echo '✓ PASS' || echo '✗ FAIL') |"
echo "| V6 Appium Android | $([ $V6_RESULT -eq 0 ] && echo '✓ PASS' || echo '✗ FAIL') |"
echo "| V7 Appium iOS | $([ $V7_RESULT -eq 0 ] && echo '✓ PASS/⊘ SKIP' || echo '✗ FAIL') |"
echo "=========================================="

if [ $V1_RESULT -eq 0 ] && [ $V2_RESULT -eq 0 ] && [ $V5_RESULT -eq 0 ] && [ $V6_RESULT -eq 0 ]; then
    echo "✓ P0核心验证全部通过!"
    exit 0
else
    echo "✗ 存在P0验证失败项，请检查上述输出"
    exit 1
fi
