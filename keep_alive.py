#!/usr/bin/env python3
"""
Railway keep-alive 스크립트
서버가 자동으로 종료되지 않도록 주기적으로 요청을 보냅니다.
"""

import requests
import time
import os
import threading

def keep_alive():
    """서버를 활성 상태로 유지"""
    url = os.getenv('RAILWAY_STATIC_URL', 'http://localhost:8080')
    health_url = f"{url}/health/"
    
    while True:
        try:
            response = requests.get(health_url, timeout=10)
            print(f"Keep-alive ping: {response.status_code}")
        except Exception as e:
            print(f"Keep-alive failed: {e}")
        
        # 30초마다 ping
        time.sleep(30)

if __name__ == "__main__":
    print("Starting keep-alive script...")
    keep_alive() 