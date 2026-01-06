FROM python:3.11-slim

# ----------------------------------------
# 1. Playwright에 필요한 시스템 라이브러리
# ----------------------------------------
RUN apt-get update && apt-get install -y \
    ca-certificates \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxshmfence1 \
    xdg-utils \
    wget \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ----------------------------------------
# 2. Python 패키지
# ----------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------
# 3. Playwright + Chromium
# ----------------------------------------
RUN pip install playwright \
 && playwright install chromium --with-deps

# ----------------------------------------
# 4. 앱 코드
# ----------------------------------------
COPY main.py .
COPY extractor.py .

# ----------------------------------------
# 5. Playwright 환경 변수 설정
# ----------------------------------------
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Chromium이 제한된 환경에서 실행되도록 설정
ENV PLAYWRIGHT_CHROMIUM_ARGS="--disable-dev-shm-usage --no-sandbox --disable-setuid-sandbox --disable-gpu"

# ----------------------------------------
# 6. 실행 (Render는 PORT 환경 변수 자동 설정)
# ----------------------------------------
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
