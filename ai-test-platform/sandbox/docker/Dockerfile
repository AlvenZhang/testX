FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/chromium /usr/bin/google-chrome

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    pytest \
    pytest-html \
    pytest-xdist \
    pytest-json-report \
    httpx \
    requests \
    selenium \
    playwright \
    jsonpath-ng

# 安装 Playwright 浏览器
RUN playwright install chromium --with-deps

# 复制执行器脚本
COPY executor/ /app/executor/

# 创建测试目录
RUN mkdir -p /app/tests /app/reports

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONPATH=/app

# 默认命令 - 运行 pytest
CMD ["python", "-m", "pytest", "/app/tests/", "-v", "--html=/app/report.html", "--self-contained-html"]
