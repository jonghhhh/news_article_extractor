FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# ----------------------------------------
# 1. Python 패키지 설치
# ----------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright는 이미 베이스 이미지에 설치되어 있으므로
# requirements.txt에서 playwright 버전만 맞춰주면 됨
# Chromium도 이미 설치되어 있음

# ----------------------------------------
# 4. 앱 코드
# ----------------------------------------
COPY main.py .
COPY extractor.py .

# ----------------------------------------
# 6. 실행 (Render는 PORT 환경 변수 자동 설정)
# ----------------------------------------
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
