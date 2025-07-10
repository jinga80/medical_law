# Python 3.8 베이스 이미지 사용
FROM python:3.8-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 정적 파일 수집
RUN python manage.py collectstatic --noinput

# 포트 노출
EXPOSE 8000

# 실행 스크립트 생성
RUN echo '#!/bin/bash\n\
python manage.py migrate\n\
python manage.py runserver 0.0.0.0:8000' > /app/start.sh \
    && chmod +x /app/start.sh

# 실행
CMD ["/app/start.sh"] 