#!/usr/bin/env python3
"""
macOS 스크린샷 캡처 스크립트
"""

import os
import time
import subprocess
import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Chrome 드라이버 초기화 실패: {e}")
        return None

def capture_with_selenium(driver, url, filename):
    """Selenium을 사용한 스크린샷 캡처"""
    try:
        print(f"캡처 중: {url}")
        driver.get(url)
        time.sleep(3)
        
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 스크린샷 저장
        screenshot_path = os.path.join("capture", filename)
        driver.save_screenshot(screenshot_path)
        print(f"✅ 스크린샷 저장됨: {screenshot_path}")
        return True
        
    except Exception as e:
        print(f"❌ 캡처 실패 {url}: {e}")
        return False

def capture_with_browser():
    """브라우저를 열어서 수동 캡처 안내"""
    base_url = "http://localhost:8000"
    
    pages = [
        ("/", "01_메인_대시보드.png"),
        ("/accounts/login/", "02_로그인_페이지.png"),
        ("/workflow/", "03_워크플로우_목록.png"),
        ("/workflow/job-requests/", "04_채용요청_목록.png"),
        ("/candidates/", "05_후보자_목록.png"),
        ("/evaluations/", "06_평가_목록.png"),
        ("/reports/", "07_보고서_목록.png"),
        ("/notifications/", "08_알림_목록.png"),
        ("/help/", "09_도움말_페이지.png"),
    ]
    
    print("🌐 브라우저를 열어서 각 페이지를 방문하세요.")
    print("📸 스크린샷을 찍고 capture 폴더에 저장하세요.")
    print("\n📋 캡처할 페이지 목록:")
    
    for i, (path, filename) in enumerate(pages, 1):
        url = base_url + path
        print(f"{i:2d}. {filename} - {url}")
    
    print(f"\n📁 저장 위치: {os.path.abspath('capture')}")
    
    # 첫 번째 페이지를 브라우저에서 열기
    first_url = base_url + pages[0][0]
    print(f"\n🚀 첫 번째 페이지를 브라우저에서 열기: {first_url}")
    webbrowser.open(first_url)

def main():
    """메인 함수"""
    print("📸 RCWS 프로젝트 스크린샷 캡처")
    print("=" * 50)
    
    # Selenium으로 시도
    driver = setup_driver()
    if driver:
        print("🔧 Selenium을 사용한 자동 캡처 시도...")
        
        base_url = "http://localhost:8000"
        pages = [
            ("/", "01_메인_대시보드.png"),
            ("/accounts/login/", "02_로그인_페이지.png"),
            ("/workflow/", "03_워크플로우_목록.png"),
            ("/workflow/job-requests/", "04_채용요청_목록.png"),
            ("/candidates/", "05_후보자_목록.png"),
            ("/evaluations/", "06_평가_목록.png"),
            ("/reports/", "07_보고서_목록.png"),
            ("/notifications/", "08_알림_목록.png"),
            ("/help/", "09_도움말_페이지.png"),
        ]
        
        success_count = 0
        for path, filename in pages:
            url = base_url + path
            if capture_with_selenium(driver, url, filename):
                success_count += 1
            time.sleep(2)
        
        driver.quit()
        
        if success_count > 0:
            print(f"\n🎉 {success_count}개 페이지 스크린샷 캡처 완료!")
        else:
            print("\n⚠️ 자동 캡처 실패. 수동 캡처를 진행합니다.")
            capture_with_browser()
    else:
        print("⚠️ Selenium 초기화 실패. 수동 캡처를 진행합니다.")
        capture_with_browser()
    
    print(f"\n📁 저장 위치: {os.path.abspath('capture')}")

if __name__ == "__main__":
    main() 