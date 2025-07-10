#!/usr/bin/env python3
"""
RCWS 프로젝트 웹 페이지 스크린샷 캡처 스크립트
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 헤드리스 모드
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

def capture_page(driver, url, filename, wait_time=3):
    """페이지 스크린샷 캡처"""
    try:
        print(f"캡처 중: {url}")
        driver.get(url)
        time.sleep(wait_time)
        
        # 페이지가 완전히 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 스크린샷 저장
        screenshot_path = os.path.join("capture", filename)
        driver.save_screenshot(screenshot_path)
        print(f"✅ 저장됨: {screenshot_path}")
        return True
        
    except Exception as e:
        print(f"❌ 캡처 실패 {url}: {e}")
        return False

def main():
    """메인 함수"""
    base_url = "http://localhost:8000"
    
    # 캡처할 페이지 목록
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
    
    # 드라이버 설정
    driver = setup_driver()
    if not driver:
        print("드라이버 초기화 실패")
        return
    
    try:
        # 각 페이지 캡처
        for path, filename in pages:
            url = base_url + path
            capture_page(driver, url, filename)
            time.sleep(2)  # 페이지 간 간격
        
        print("\n🎉 모든 스크린샷 캡처 완료!")
        print(f"📁 저장 위치: {os.path.abspath('capture')}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 