from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Organization, UserActivity
from notifications.models import NotificationPreference
from workflow.models import JobRequest, WorkflowProgress, JobPosting
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = '초기 기관 및 사용자 데이터를 생성합니다.'

    def handle(self, *args, **options):
        self.stdout.write('초기 데이터 생성을 시작합니다...')
        
        # 기관 생성
        organizations = self.create_organizations()
        
        # 사용자 생성
        users = self.create_users(organizations)
        
        # 알림 설정 생성
        self.create_notification_preferences(users)
        
        # WorkflowProgress 초기 데이터 생성
        for job_request in JobRequest.objects.all():
            # 목표 완료일을 2주 후로 설정
            target_date = date.today() + timedelta(days=14)
            
            WorkflowProgress.objects.get_or_create(
                job_request=job_request,
                defaults={
                    'target_completion_date': target_date,
                    'current_step': 'job_request',
                    'step_completion_rate': 100 if job_request.status != 'draft' else 0,
                }
            )
        
        # JobPosting 초기 데이터 생성 (샘플)
        sample_job_request = JobRequest.objects.first()
        if sample_job_request:
            JobPosting.objects.get_or_create(
                job_request=sample_job_request,
                defaults={
                    'created_by': users['mediking_admin'],
                    'title': f"{sample_job_request.position_title} 채용 공고",
                    'summary': f"{sample_job_request.department} 부서 {sample_job_request.position_title} 포지션을 모집합니다.",
                    'detailed_description': sample_job_request.job_description,
                    'requirements': sample_job_request.required_experience,
                    'preferred_qualifications': sample_job_request.preferred_qualifications,
                    'benefits': "4대보험, 퇴직연금, 경조사 지원, 교육비 지원",
                    'posting_date': timezone.now(),
                    'closing_date': timezone.now() + timedelta(days=30),
                    'application_deadline': timezone.now() + timedelta(days=25),
                    'status': 'published',
                    'is_featured': True
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS('초기 데이터 생성이 완료되었습니다!')
        )

    def create_organizations(self):
        """기관 생성"""
        organizations = {}
        
        # 리버스 클리닉
        hospital, created = Organization.objects.get_or_create(
            name='리버스 클리닉',
            defaults={
                'org_type': 'hospital',
                'address': '서울특별시 강남구 테헤란로 123',
                'phone': '02-1234-5678',
                'email': 'hr@reverseclinic.com',
                'description': '리버스 클리닉 인사팀'
            }
        )
        if created:
            self.stdout.write(f'기관 생성: {hospital.name}')
        organizations['hospital'] = hospital
        
        # 케이지아웃소싱
        headhunting, created = Organization.objects.get_or_create(
            name='케이지아웃소싱',
            defaults={
                'org_type': 'headhunting',
                'address': '서울특별시 강남구 역삼동 456',
                'phone': '02-9876-5432',
                'email': 'info@casejoutsourcing.com',
                'description': '헤드헌팅 전문 회사'
            }
        )
        if created:
            self.stdout.write(f'기관 생성: {headhunting.name}')
        organizations['headhunting'] = headhunting
        
        # 메디킹 관리기관
        admin_org, created = Organization.objects.get_or_create(
            name='메디킹',
            defaults={
                'org_type': 'admin',
                'address': '서울특별시 강남구 삼성동 789',
                'phone': '02-5555-1234',
                'email': 'admin@mediking.com',
                'description': 'RCWS 시스템 관리기관'
            }
        )
        if created:
            self.stdout.write(f'기관 생성: {admin_org.name}')
        organizations['admin'] = admin_org
        
        return organizations

    def create_users(self, organizations):
        """사용자 생성"""
        users = {}
        
        # 리버스 클리닉 사용자들
        hospital_users = [
            {
                'username': 'hospital_hr1',
                'email': 'hr1@reverseclinic.com',
                'first_name': '김',
                'last_name': '인사',
                'role': 'hospital_hr',
                'phone': '010-1111-1111',
                'department': '인사팀',
                'position': '인사담당자'
            },
            {
                'username': 'hospital_manager1',
                'email': 'manager1@reverseclinic.com',
                'first_name': '박',
                'last_name': '관리',
                'role': 'hospital_manager',
                'phone': '010-2222-2222',
                'department': '간호팀',
                'position': '간호팀장'
            }
        ]
        
        for user_data in hospital_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'organization': organizations['hospital'],
                    'role': user_data['role'],
                    'phone': user_data['phone'],
                    'department': user_data['department'],
                    'position': user_data['position'],
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                user.set_password('1234')
                user.save()
                self.stdout.write(f'사용자 생성: {user.get_full_name()}')
            users[user_data['username']] = user
        
        # 케이지아웃소싱 사용자들
        headhunting_users = [
            {
                'username': 'kim_taegyun',
                'email': 'kim.taegyun@casejoutsourcing.com',
                'first_name': '김',
                'last_name': '태균',
                'role': 'hh_ceo',
                'phone': '010-3333-3333',
                'department': '경영진',
                'position': '대표'
            },
            {
                'username': 'kim_nakyung',
                'email': 'kim.nakyung@casejoutsourcing.com',
                'first_name': '김',
                'last_name': '나경',
                'role': 'hh_manager',
                'phone': '010-4444-4444',
                'department': '채용팀',
                'position': '팀장'
            },
            {
                'username': 'lee_nahyun',
                'email': 'lee.nahyun@casejoutsourcing.com',
                'first_name': '이',
                'last_name': '나현',
                'role': 'hh_staff',
                'phone': '010-5555-5555',
                'department': '채용팀',
                'position': '대리'
            }
        ]
        
        for user_data in headhunting_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'organization': organizations['headhunting'],
                    'role': user_data['role'],
                    'phone': user_data['phone'],
                    'department': user_data['department'],
                    'position': user_data['position'],
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                user.set_password('1234')
                user.save()
                self.stdout.write(f'사용자 생성: {user.get_full_name()}')
            users[user_data['username']] = user
        
        # 메디킹 관리자
        admin_user, created = User.objects.get_or_create(
            username='mediking_admin',
            defaults={
                'email': 'admin@mediking.com',
                'first_name': '메디킹',
                'last_name': '관리자',
                'organization': organizations['admin'],
                'role': 'system_admin',
                'phone': '010-6666-6666',
                'department': '시스템관리팀',
                'position': '시스템관리자',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        if created:
            admin_user.set_password('admin')
            admin_user.save()
            self.stdout.write(f'관리자 생성: {admin_user.get_full_name()}')
        users['mediking_admin'] = admin_user
        
        return users

    def create_notification_preferences(self, users):
        """알림 설정 생성"""
        for username, user in users.items():
            preference, created = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'email_notifications': True,
                    'web_notifications': True,
                    'sms_notifications': False,
                    'job_request_notifications': True,
                    'candidate_notifications': True,
                    'interview_notifications': True,
                    'workflow_notifications': True,
                    'system_notifications': True
                }
            )
            if created:
                self.stdout.write(f'알림 설정 생성: {user.get_full_name()}') 