# RCWS API 사용 예시

## 기본 정보
- **Base URL**: `http://localhost:8000/api/`
- **인증**: Session Authentication (로그인 필요)
- **문서**: `http://localhost:8000/api/swagger/`

## 1. 채용 요청 API

### 1.1 채용 요청 생성
```bash
curl -X POST "http://localhost:8000/api/job-requests/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session_id" \
  -d '{
    "position_title": "내과 전문의",
    "department": "내과",
    "employment_type": "full_time",
    "salary_min": 8000,
    "salary_max": 12000,
    "required_experience": "5년 이상의 내과 경력",
    "preferred_qualifications": "대학병원 경력 우대",
    "job_description": "내과 환자 진료 및 치료",
    "working_hours": "주 5일, 40시간",
    "working_location": "서울시 강남구",
    "urgency_level": "high"
  }'
```

### 1.2 채용 요청 제출
```bash
curl -X POST "http://localhost:8000/api/job-requests/{id}/submit/" \
  -H "Cookie: sessionid=your_session_id"
```

### 1.3 채용 요청 접수
```bash
curl -X POST "http://localhost:8000/api/job-requests/{id}/accept/" \
  -H "Cookie: sessionid=your_session_id"
```

## 2. 후보자 API

### 2.1 후보자 생성
```bash
curl -X POST "http://localhost:8000/api/candidates/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session_id" \
  -d '{
    "name": "김의사",
    "email": "kim@doctor.com",
    "phone": "010-1234-5678",
    "job_request": 1,
    "notes": "우수한 내과 전문의, 10년 경력"
  }'
```

### 2.2 후보자 승인
```bash
curl -X POST "http://localhost:8000/api/candidates/{id}/approve/" \
  -H "Cookie: sessionid=your_session_id"
```

### 2.3 후보자 거절
```bash
curl -X POST "http://localhost:8000/api/candidates/{id}/reject/" \
  -H "Cookie: sessionid=your_session_id"
```

## 3. 면접 API

### 3.1 면접 생성
```bash
curl -X POST "http://localhost:8000/api/interviews/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session_id" \
  -d '{
    "candidate": 1,
    "interviewer": 2,
    "scheduled_date": "2024-01-15T14:00:00Z",
    "location": "서울시 강남구 테헤란로 123",
    "interview_type": "face_to_face",
    "notes": "1차 면접"
  }'
```

### 3.2 면접 완료
```bash
curl -X POST "http://localhost:8000/api/interviews/{id}/complete/" \
  -H "Cookie: sessionid=your_session_id"
```

## 4. 알림 API

### 4.1 알림 목록 조회
```bash
curl -X GET "http://localhost:8000/api/notifications/" \
  -H "Cookie: sessionid=your_session_id"
```

### 4.2 알림 읽음 처리
```bash
curl -X POST "http://localhost:8000/api/notifications/{id}/mark_read/" \
  -H "Cookie: sessionid=your_session_id"
```

### 4.3 읽지 않은 알림 개수
```bash
curl -X GET "http://localhost:8000/api/notifications/unread_count/" \
  -H "Cookie: sessionid=your_session_id"
```

## 5. 대시보드 API

### 5.1 대시보드 통계
```bash
curl -X GET "http://localhost:8000/api/dashboard/stats/" \
  -H "Cookie: sessionid=your_session_id"
```

### 5.2 최근 활동
```bash
curl -X GET "http://localhost:8000/api/dashboard/recent-activities/" \
  -H "Cookie: sessionid=your_session_id"
```

## 6. 보고서 API

### 6.1 성과 보고서
```bash
curl -X GET "http://localhost:8000/api/reports/performance/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Cookie: sessionid=your_session_id"
```

### 6.2 워크플로우 분석
```bash
curl -X GET "http://localhost:8000/api/reports/workflow-analytics/" \
  -H "Cookie: sessionid=your_session_id"
```

## JavaScript 예시

### Axios를 사용한 예시
```javascript
import axios from 'axios';

// 기본 설정
axios.defaults.baseURL = 'http://localhost:8000/api';
axios.defaults.withCredentials = true; // 쿠키 포함

// 채용 요청 생성
const createJobRequest = async (data) => {
  try {
    const response = await axios.post('/job-requests/', data);
    return response.data;
  } catch (error) {
    console.error('Error creating job request:', error);
    throw error;
  }
};

// 후보자 목록 조회
const getCandidates = async () => {
  try {
    const response = await axios.get('/candidates/');
    return response.data;
  } catch (error) {
    console.error('Error fetching candidates:', error);
    throw error;
  }
};

// 알림 읽음 처리
const markNotificationRead = async (notificationId) => {
  try {
    const response = await axios.post(`/notifications/${notificationId}/mark_read/`);
    return response.data;
  } catch (error) {
    console.error('Error marking notification read:', error);
    throw error;
  }
};
```

### React Hook 예시
```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

const useJobRequests = () => {
  const [jobRequests, setJobRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchJobRequests = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/job-requests/');
        setJobRequests(response.data.results || response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchJobRequests();
  }, []);

  const createJobRequest = async (data) => {
    try {
      const response = await axios.post('/job-requests/', data);
      setJobRequests(prev => [response.data, ...prev]);
      return response.data;
    } catch (err) {
      setError(err);
      throw err;
    }
  };

  return { jobRequests, loading, error, createJobRequest };
};
```

## Python 예시

### requests 라이브러리 사용
```python
import requests

class RCWSClient:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, username, password):
        """로그인하여 세션 생성"""
        login_url = "http://localhost:8000/login/"
        response = self.session.post(login_url, data={
            'username': username,
            'password': password
        })
        return response.status_code == 200
    
    def create_job_request(self, data):
        """채용 요청 생성"""
        response = self.session.post(f"{self.base_url}/job-requests/", json=data)
        return response.json()
    
    def get_candidates(self):
        """후보자 목록 조회"""
        response = self.session.get(f"{self.base_url}/candidates/")
        return response.json()
    
    def approve_candidate(self, candidate_id):
        """후보자 승인"""
        response = self.session.post(f"{self.base_url}/candidates/{candidate_id}/approve/")
        return response.json()

# 사용 예시
client = RCWSClient()
if client.login("hospital_user", "password123"):
    # 채용 요청 생성
    job_request = client.create_job_request({
        "position_title": "외과 전문의",
        "department": "외과",
        "employment_type": "full_time",
        "required_experience": "3년 이상",
        "job_description": "외과 수술 및 진료"
    })
    print(f"Created job request: {job_request}")
```

## 에러 처리

### 일반적인 HTTP 상태 코드
- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 필요
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `500 Internal Server Error`: 서버 오류

### 에러 응답 예시
```json
{
  "error": "이미 제출된 요청입니다.",
  "detail": "Cannot submit already submitted request"
}
```

## 인증 및 권한

### 사용자 역할별 권한
- **병원 사용자**: 채용 요청 생성/수정, 후보자 검토, 면접 일정 조율
- **헤드헌팅 사용자**: 채용 요청 접수, 후보자 추천, 면접 평가
- **관리자**: 모든 기능 접근 가능

### 권한 확인
```javascript
// 현재 사용자 정보 조회
const getCurrentUser = async () => {
  const response = await axios.get('/users/profile/');
  return response.data;
};

// 권한 확인
const checkPermission = (user, requiredRole) => {
  return user.role === requiredRole || user.role === 'system_admin';
};
``` 