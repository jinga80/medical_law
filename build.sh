#!/bin/bash
# Railway 배포용 빌드 스크립트

echo "🚀 Railway 배포 시작..."

# Python 버전 확인
python --version

# 의존성 설치
echo "📦 의존성 설치 중..."
pip install -r requirements.txt

# 정적 파일 수집
echo "📁 정적 파일 수집 중..."
python manage.py collectstatic --noinput

# 데이터베이스 마이그레이션
echo "🗄️ 데이터베이스 마이그레이션 중..."
python manage.py migrate

echo "✅ 빌드 완료!" 