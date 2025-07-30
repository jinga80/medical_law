#!/bin/bash
# Railway 배포용 엔트리포인트 스크립트

echo "🚀 의료광고법 준수 검토 시스템 시작..."

# 데이터베이스 마이그레이션
echo "🗄️ 데이터베이스 마이그레이션 중..."
python manage.py migrate

# 정적 파일 수집 (필요한 경우)
echo "📁 정적 파일 수집 중..."
python manage.py collectstatic --noinput

# 서버 시작 (keep-alive 설정 추가)
echo "🌐 서버 시작 중..."

# 백그라운드에서 keep-alive 스크립트 실행
python keep_alive.py &
KEEP_ALIVE_PID=$!

# 메인 서버 시작
exec gunicorn medical_law_project.wsgi:application --bind 0.0.0.0:$PORT --keep-alive 2 --timeout 120 