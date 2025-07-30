# Python 3.9 이미지 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 엔트리포인트 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 포트 설정
EXPOSE 8000

# 엔트리포인트 스크립트 실행
ENTRYPOINT ["./entrypoint.sh"] 