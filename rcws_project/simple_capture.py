#!/usr/bin/env python3
"""
간단한 웹 페이지 캡처 스크립트
"""

import os
import time
import requests
from PIL import Image
import io

def capture_page_simple(url, filename):
    """간단한 페이지 캡처 (HTML 내용 저장)"""
    try:
        print(f"캡처 중: {url}")
        
        # 페이지 내용 가져오기
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # HTML 내용을 파일로 저장
        html_path = os.path.join("capture", filename.replace('.png', '.html'))
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✅ HTML 저장됨: {html_path}")
        return True
        
    except Exception as e:
        print(f"❌ 캡처 실패 {url}: {e}")
        return False

def main():
    """메인 함수"""
    base_url = "http://localhost:8000"
    
    # 캡처할 페이지 목록
    pages = [
        ("/", "01_메인_대시보드"),
        ("/accounts/login/", "02_로그인_페이지"),
        ("/workflow/", "03_워크플로우_목록"),
        ("/workflow/job-requests/", "04_채용요청_목록"),
        ("/candidates/", "05_후보자_목록"),
        ("/evaluations/", "06_평가_목록"),
        ("/reports/", "07_보고서_목록"),
        ("/notifications/", "08_알림_목록"),
        ("/help/", "09_도움말_페이지"),
    ]
    
    print("🌐 RCWS 프로젝트 웹 페이지 캡처 시작...")
    
    # 각 페이지 캡처
    for path, filename in pages:
        url = base_url + path
        capture_page_simple(url, filename)
        time.sleep(1)  # 페이지 간 간격
    
    print("\n🎉 모든 페이지 캡처 완료!")
    print(f"📁 저장 위치: {os.path.abspath('capture')}")
    
    # README 파일 생성
    create_readme()

def create_readme():
    """README 파일 생성"""
    readme_content = """# RCWS 프로젝트 웹 페이지 캡처

이 폴더에는 RCWS 프로젝트의 주요 웹 페이지들이 캡처되어 있습니다.

## 📋 캡처된 페이지 목록

1. **01_메인_대시보드.html** - 메인 대시보드 페이지
2. **02_로그인_페이지.html** - 사용자 로그인 페이지
3. **03_워크플로우_목록.html** - 워크플로우 관리 페이지
4. **04_채용요청_목록.html** - 채용 요청 목록 페이지
5. **05_후보자_목록.html** - 후보자 관리 페이지
6. **06_평가_목록.html** - 평가 관리 페이지
7. **07_보고서_목록.html** - 보고서 페이지
8. **08_알림_목록.html** - 알림 관리 페이지
9. **09_도움말_페이지.html** - 도움말 페이지

## 🎨 주요 디자인 특징

- **반응형 디자인**: 모바일과 데스크톱 모두 지원
- **현대적 UI**: Font Awesome 아이콘과 그라데이션 효과
- **실시간 업데이트**: 30초마다 자동 데이터 갱신
- **색상 테마**: 각 프로세스 단계별 고유 색상
- **애니메이션**: 부드러운 호버 효과와 전환 애니메이션

## 🚀 기술 스택

- **Backend**: Django 4.2.7
- **Frontend**: HTML5, CSS3, JavaScript
- **아이콘**: Font Awesome 6.4.0
- **스타일링**: Bootstrap + 커스텀 CSS

## 📱 사용자 역할

1. **시스템 관리자** (admin/1234)
2. **병원 사용자** (reverse/1234)
3. **헤드헌팅 사용자** (hr1/1234)

캡처 날짜: """ + time.strftime("%Y년 %m월 %d일 %H:%M") + """

---
*RCWS (Recruitment Collaboration Workflow System) - 병원과 헤드헌팅 회사의 협업 채용 시스템*
"""
    
    readme_path = os.path.join("capture", "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📝 README 파일 생성: {readme_path}")

if __name__ == "__main__":
    main() 