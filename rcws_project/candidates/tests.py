from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Candidate
from workflow.models import JobRequest
from accounts.models import Organization
from django.utils import timezone

User = get_user_model()


class CandidateAPITestCase(APITestCase):
    def setUp(self):
        # 테스트용 기관 생성
        self.hospital = Organization.objects.create(
            name="테스트 병원",
            org_type="hospital"
        )
        self.headhunting = Organization.objects.create(
            name="테스트 헤드헌팅",
            org_type="headhunting"
        )
        
        # 테스트용 사용자 생성
        self.hospital_user = User.objects.create_user(
            username="hospital_user",
            password="testpass123",
            email="hospital@test.com",
            organization=self.hospital,
            role="hospital_hr"
        )
        self.headhunting_user = User.objects.create_user(
            username="headhunting_user",
            password="testpass123",
            email="headhunting@test.com",
            organization=self.headhunting,
            role="hh_ceo"
        )
        
        # 테스트용 채용 요청 생성
        self.job_request = JobRequest.objects.create(
            requester=self.hospital_user,
            position_title="내과 전문의",
            department="내과",
            employment_type="full_time",
            required_experience="5년 이상",
            job_description="내과 환자 진료"
        )
        
        self.client = APIClient()
    
    def test_create_candidate(self):
        """후보자 생성 테스트"""
        self.client.force_authenticate(user=self.headhunting_user)
        
        data = {
            "name": "김의사",
            "email": "kim@doctor.com",
            "phone": "010-1234-5678",
            "job_request": self.job_request.id,
            "notes": "우수한 내과 전문의"
        }
        
        response = self.client.post('/api/candidates/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Candidate.objects.count(), 1)
        self.assertEqual(response.data['name'], "김의사")
    
    def test_approve_candidate(self):
        """후보자 승인 테스트"""
        candidate = Candidate.objects.create(
            name="이의사",
            email="lee@doctor.com",
            phone="010-9876-5432",
            job_request=self.job_request,
            recommended_by=self.headhunting_user,
            status="recommended"
        )
        
        self.client.force_authenticate(user=self.hospital_user)
        response = self.client.post(f'/api/candidates/{candidate.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, 'approved')
    
    def test_reject_candidate(self):
        """후보자 거절 테스트"""
        candidate = Candidate.objects.create(
            name="박의사",
            email="park@doctor.com",
            phone="010-1111-2222",
            job_request=self.job_request,
            recommended_by=self.headhunting_user,
            status="recommended"
        )
        
        self.client.force_authenticate(user=self.hospital_user)
        response = self.client.post(f'/api/candidates/{candidate.id}/reject/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, 'rejected')
    
    def test_my_recommendations(self):
        """내가 추천한 후보자 목록 테스트"""
        candidate1 = Candidate.objects.create(
            name="최의사",
            email="choi@doctor.com",
            phone="010-3333-4444",
            job_request=self.job_request,
            recommended_by=self.headhunting_user
        )
        candidate2 = Candidate.objects.create(
            name="정의사",
            email="jung@doctor.com",
            phone="010-5555-6666",
            job_request=self.job_request,
            recommended_by=self.headhunting_user
        )
        
        self.client.force_authenticate(user=self.headhunting_user)
        response = self.client.get('/api/candidates/my_recommendations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
