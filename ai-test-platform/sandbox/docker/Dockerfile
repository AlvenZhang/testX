FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-html \
    pytest-xdist \
    selenium \
    playwright \
    httpx \
    requests

# Copy executor scripts
COPY executor/ /app/executor/

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Run tests
CMD ["python", "-m", "pytest", "/app/tests/", "--html=/app/report.html", "--self-contained-html"]
