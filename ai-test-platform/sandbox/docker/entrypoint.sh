#!/bin/bash
# Docker 沙箱容器入口脚本

set -e

echo "=========================================="
echo "AI Test Platform - Sandbox Container"
echo "=========================================="

# 配置
export PYTHONUNBUFFERED=1
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 创建必要的目录
mkdir -p /app/tests /app/reports /app/screenshots /tmp

# 检查环境
echo "Checking environment..."
python --version
echo "Chrome/Chromium: $(which chromium || which google-chrome || echo 'Not found')"

# 预热 Playwright
if command -v playwright &> /dev/null; then
    echo "Installing Playwright browsers..."
    playwright install chromium --with-deps 2>/dev/null || true
fi

# 处理命令行参数
CMD="$1"

case "$CMD" in
    "pytest")
        echo "Running pytest..."
        shift
        python -m pytest "$@"
        ;;

    "api")
        echo "Running API tests..."
        shift
        python /app/executor/api_executor.py "$@"
        ;;

    "web")
        echo "Running Web UI tests..."
        shift
        python /app/executor/web_executor.py "$@"
        ;;

    "mobile")
        echo "Running Mobile tests..."
        shift
        python /app/executor/run_mobile_test.py "$@"
        ;;

    "unit")
        echo "Running Unit tests..."
        shift
        python /app/executor/run_unit_test.py "$@"
        ;;

    "shell")
        echo "Starting shell..."
        /bin/bash
        ;;

    "sleep")
        echo "Container ready, sleeping..."
        sleep infinity
        ;;

    *)
        echo "Usage:"
        echo "  $0 pytest [args]     - Run pytest"
        echo "  $0 api [args]       - Run API tests"
        echo "  $0 web [args]       - Run Web UI tests"
        echo "  $0 mobile [args]   - Run Mobile tests"
        echo "  $0 unit [args]      - Run Unit tests"
        echo "  $0 shell            - Start interactive shell"
        echo "  $0 sleep            - Sleep forever"
        echo ""
        echo "Default: Running pytest..."
        python -m pytest /app/tests/ -v --tb=short
        ;;
esac
