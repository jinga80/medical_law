from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import JobRequest, WorkflowStep
from accounts.models import Organization
from django.utils import timezone

User = get_user_model()


class JobRequestAPITestCase(APITestCase):
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
        
        self.client = APIClient()
    
    def test_create_job_request(self):
        """채용 요청 생성 테스트"""
        self.client.force_authenticate(user=self.hospital_user)
        
        data = {
            "position_title": "내과 전문의",
            "department": "내과",
            "employment_type": "full_time",
            "salary_min": 8000,
            "salary_max": 12000,
            "required_experience": "5년 이상의 내과 경력",
            "job_description": "내과 환자 진료 및 치료",
            "urgency_level": "high"
        }
        
        response = self.client.post('/api/job-requests/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobRequest.objects.count(), 1)
        self.assertEqual(response.data['position_title'], "내과 전문의")
    
    def test_submit_job_request(self):
        """채용 요청 제출 테스트"""
        job_request = JobRequest.objects.create(
            requester=self.hospital_user,
            position_title="외과 전문의",
            department="외과",
            employment_type="full_time",
            required_experience="3년 이상",
            job_description="외과 수술 및 진료"
        )
        
        self.client.force_authenticate(user=self.hospital_user)
        response = self.client.post(f'/api/job-requests/{job_request.id}/submit/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        job_request.refresh_from_db()
        self.assertEqual(job_request.status, 'submitted')
    
    def test_accept_job_request(self):
        """채용 요청 접수 테스트"""
        job_request = JobRequest.objects.create(
            requester=self.hospital_user,
            position_title="소아과 전문의",
            department="소아과",
            employment_type="full_time",
            required_experience="3년 이상",
            job_description="소아 진료",
            status='submitted',
            submitted_at=timezone.now()
        )
        
        self.client.force_authenticate(user=self.headhunting_user)
        response = self.client.post(f'/api/job-requests/{job_request.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        job_request.refresh_from_db()
        self.assertEqual(job_request.status, 'accepted')


class WorkflowStepAPITestCase(APITestCase):
    def setUp(self):
        self.hospital = Organization.objects.create(
            name="테스트 병원",
            org_type="hospital"
        )
        self.hospital_user = User.objects.create_user(
            username="hospital_user",
            password="testpass123",
            email="hospital@test.com",
            organization=self.hospital,
            role="hospital_hr"
        )
        
        self.job_request = JobRequest.objects.create(
            requester=self.hospital_user,
            position_title="정형외과 전문의",
            department="정형외과",
            employment_type="full_time",
            required_experience="5년 이상",
            job_description="정형외과 수술 및 진료"
        )
        
        self.workflow_step = WorkflowStep.objects.create(
            job_request=self.job_request,
            step_name="document_review",
            status="pending"
        )
        
        self.client = APIClient()
    
    def test_start_workflow_step(self):
        """워크플로우 단계 시작 테스트"""
        self.client.force_authenticate(user=self.hospital_user)
        
        response = self.client.post(f'/api/workflow-steps/{self.workflow_step.id}/start/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.workflow_step.refresh_from_db()
        self.assertEqual(self.workflow_step.status, 'in_progress')
        self.assertIsNotNone(self.workflow_step.started_at)
    
    def test_complete_workflow_step(self):
        """워크플로우 단계 완료 테스트"""
        self.workflow_step.status = 'in_progress'
        self.workflow_step.started_at = timezone.now()
        self.workflow_step.save()
        
        self.client.force_authenticate(user=self.hospital_user)
        
        response = self.client.post(f'/api/workflow-steps/{self.workflow_step.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.workflow_step.refresh_from_db()
        self.assertEqual(self.workflow_step.status, 'completed')
        self.assertIsNotNone(self.workflow_step.completed_at)
