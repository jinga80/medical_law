# 의료광고법 준수 검토 시스템

## 📋 프로젝트 개요

의료광고법 준수 검토 시스템은 의료기관의 광고물이 의료광고법을 준수하는지 자동으로 분석하고 검토하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **텍스트 분석**: 광고 텍스트의 준수 여부 자동 검토
- **파일 분석**: PDF, Word 문서 등 다양한 형식 지원
- **URL 분석**: 웹페이지 광고 내용 분석
- **AI 기반 개선**: Claude AI를 활용한 맞춤형 개선 방안 제시
- **히스토리 관리**: 분석 결과 저장 및 관리
- **대시보드**: 분석 통계 및 현황 제공

## 🛠 기술 스택

- **Backend**: Django 4.2.23
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **AI**: Anthropic Claude API
- **Database**: SQLite (개발) / PostgreSQL (배포)
- **Deployment**: Railway, Render, Heroku 지원

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/jinga80/medical_law.git
cd medical_law
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
# .env 파일 생성
ANTHROPIC_API_KEY=your_api_key_here
DEBUG=True
SECRET_KEY=your_secret_key_here
```

### 5. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

### 6. 서버 실행
```bash
python manage.py runserver
```

## 🌐 배포

### Railway 배포 (추천)
1. GitHub 저장소를 Railway에 연결
2. 환경변수 설정
3. 자동 배포 완료

### Render 배포
1. Render.com에서 Web Service 생성
2. GitHub 저장소 연결
3. 환경변수 설정

## 📊 사용법

1. **새 분석 시작**: 메인 페이지에서 텍스트, 파일, URL 입력
2. **분석 결과 확인**: 준수 점수, 위반 항목, 개선 방안 확인
3. **히스토리 관리**: 이전 분석 결과 조회 및 관리
4. **대시보드**: 전체 분석 통계 확인

## 🔧 개발 환경 설정

### 필요한 패키지
- Django 4.2.23
- PyPDF2 3.0.1
- python-docx 1.1.2
- beautifulsoup4 4.13.4
- requests 2.32.4
- selenium 4.27.1
- anthropic 0.7.0+

### 개발 서버 실행
```bash
python manage.py runserver
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.
