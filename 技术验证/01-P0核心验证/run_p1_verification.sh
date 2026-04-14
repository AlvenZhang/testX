#!/bin/bash
# P1 技术验证汇总脚本
# 运行: ./run_p1_verification.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "P1 技术验证"
echo "========================================"
echo ""

# 定义颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 记录结果
PASSED=0
FAILED=0
SKIPPED=0

# 运行单个验证
run_verify() {
    local name=$1
    local script=$2

    echo "----------------------------------------"
    echo "运行: $name"
    echo "----------------------------------------"

    if python "$script"; then
        echo -e "${GREEN}✓ $name: PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ $name: FAIL${NC}"
        ((FAILED++))
    fi
    echo ""
}

# V3: Redis 缓存测试
run_verify "V3 Redis 缓存" "verify_v3_redis_cache.py"

# V8: AI 影响分析
run_verify "V8 AI 影响分析" "verify_v8_ai_impact_analysis.py"

# V9: AI 测试用例生成
run_verify "V9 AI 测试用例生成" "verify_v9_ai_test_case_generation.py"

# V10: AI 测试代码生成
run_verify "V10 AI 测试代码生成" "verify_v10_ai_test_code_generation.py"

# V11: AI 测试方案生成
run_verify "V11 AI 测试方案生成" "verify_v11_ai_test_plan_generation.py"

# 汇总
echo "========================================"
echo "P1 验证汇总"
echo "========================================"
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo -e "跳过: ${YELLOW}$SKIPPED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ P1 验证全部通过${NC}"
    exit 0
else
    echo -e "${RED}✗ P1 验证存在失败项${NC}"
    exit 1
fi