from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Organization, Branch
from workflow.models import JobRequestTemplate
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = '리버스클리닉 홍대점 채용 기획안에 맞춰 직책별 템플릿을 생성합니다.'

    def handle(self, *args, **options):
        self.stdout.write('채용 요청 템플릿 생성을 시작합니다...')
        
        # 관리자 사용자 찾기
        try:
            admin_user = User.objects.filter(role='system_admin').first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('시스템 관리자 사용자를 찾을 수 없습니다.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'사용자 조회 중 오류: {e}'))
            return
        
        # 리버스클리닉 기관 찾기
        try:
            hospital_org = Organization.objects.filter(
                org_type='hospital',
                name__icontains='리버스클리닉'
            ).first()
            
            if not hospital_org:
                # 기관이 없으면 생성
                hospital_org = Organization.objects.create(
                    name='리버스클리닉',
                    org_type='hospital',
                    address='서울특별시 마포구 홍대로 123',
                    phone='02-1234-5678',
                    email='hr@reverseclinic.com',
                    description='피부과 전문 의료기관'
                )
                self.stdout.write(f'리버스클리닉 기관을 생성했습니다: {hospital_org.name}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'기관 조회/생성 중 오류: {e}'))
            return
        
        # 홍대점 지점 찾기
        try:
            hongdae_branch = Branch.objects.filter(
                organization=hospital_org,
                name__icontains='홍대'
            ).first()
            
            if not hongdae_branch:
                # 지점이 없으면 생성
                hongdae_branch = Branch.objects.create(
                    organization=hospital_org,
                    name='홍대점',
                    address='서울특별시 마포구 홍대로 123 4층',
                    phone='02-1234-5678',
                    email='hongdae@reverseclinic.com',
                    manager_name='김지점장',
                    manager_phone='010-1234-5678',
                    description='리버스클리닉 홍대점'
                )
                self.stdout.write(f'홍대점을 생성했습니다: {hongdae_branch.get_full_name()}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'지점 조회/생성 중 오류: {e}'))
            return
        
        # 기존 템플릿 삭제 (선택사항)
        if options.get('clear_existing', False):
            JobRequestTemplate.objects.all().delete()
            self.stdout.write('기존 템플릿을 모두 삭제했습니다.')
        
        # 템플릿 생성
        templates_data = [
            {
                'name': '총괄실장 채용 템플릿',
                'description': '리버스클리닉 홍대점 총괄실장 채용용 템플릿',
                'position_title': '총괄실장',
                'department': '경영관리팀',
                'employment_type': 'full_time',
                'salary_min': 3500,
                'salary_max': 4500,
                'required_experience': '''• 30대 후반 이상
• 의료기관 운영 경험 5년 이상
• 인력 관리 및 운영 총괄 경험
• 빠른 현장 적응력과 리더십
• 문제 해결 능력 우수''',
                'preferred_qualifications': '''• 피부과 의원 운영 경험
• 의료진과의 원활한 소통 능력
• 고객 서비스 마인드
• 업무 효율성 개선 경험''',
                'job_description': '''• 전체 인력 및 운영 총괄
• 실시간 문제 해결 및 현장 관리
• 상담실장 지원 및 업무 조율
• 신규 인력 온보딩 및 교육
• 고객 응대 및 예약 관리
• 시술실 환경 관리''',
                'working_hours': '평일 09:00-18:00 (점심시간 12:00-13:00)',
                'working_location': '리버스클리닉 홍대점',
                'urgency_level': 'medium'
            },
            {
                'name': '상담실장 채용 템플릿',
                'description': '리버스클리닉 홍대점 상담실장 채용용 템플릿',
                'position_title': '상담실장',
                'department': '상담팀',
                'employment_type': 'full_time',
                'salary_min': 2800,
                'salary_max': 3500,
                'required_experience': '''• 28~35세 선호
• 상담 업무 경험 3년 이상
• 고객 응대 및 서비스 경험
• 예약 및 일정 관리 경험
• 총괄실장보다 약간 어린 연령대''',
                'preferred_qualifications': '''• 피부과 상담 경험
• 의료 상담사 자격증
• 고객 만족도 관리 경험
• 상담 데이터 관리 경험''',
                'job_description': '''• 고객 상담 및 시술 안내 (전체 상담의 90% 전담)
• 예약 및 일정 관리
• 상담 데이터 관리
• 총괄실장 업무 일부 지원
• 고객 응대 및 예약
• 시술실 환경 관리''',
                'working_hours': '평일 09:00-18:00 (점심시간 12:00-13:00)',
                'working_location': '리버스클리닉 홍대점',
                'urgency_level': 'medium'
            },
            {
                'name': '코디네이터 채용 템플릿',
                'description': '리버스클리닉 홍대점 코디네이터 채용용 템플릿',
                'position_title': '코디네이터',
                'department': '상담팀',
                'employment_type': 'full_time',
                'salary_min': 2200,
                'salary_max': 2800,
                'required_experience': '''• 상담실장 인원에 따라 1명 배치
• 고객 응대 및 안내 경험
• 예약 및 일정 관리 경험
• 상담실장 보조 업무 경험''',
                'preferred_qualifications': '''• 피부과 관련 업무 경험
• 고객 서비스 마인드
• 업무 효율성 개선 능력
• 팀워크 능력''',
                'job_description': '''• 상담실장 보조
• 고객 응대 및 안내
• 예약 및 일정 조정
• 고객 응대 및 예약
• 시술실 환경 관리''',
                'working_hours': '평일 09:00-18:00 (점심시간 12:00-13:00)',
                'working_location': '리버스클리닉 홍대점',
                'urgency_level': 'low'
            },
            {
                'name': '피부팀장 채용 템플릿',
                'description': '리버스클리닉 홍대점 피부팀장 채용용 템플릿',
                'position_title': '피부팀장',
                'department': '피부팀',
                'employment_type': 'full_time',
                'salary_min': 3200,
                'salary_max': 4000,
                'required_experience': '''• 경력자(팀장급) 우대
• 피부관리 및 레이저 시술 경험 5년 이상
• 팀 관리 및 교육 경험
• 시술 프로토콜 관리 경험
• 신입 교육 및 관리 경험''',
                'preferred_qualifications': '''• 피부과 전문 경험
• 레이저 시술 전문가 자격
• 팀 리더십 경험
• 시술 품질 관리 경험''',
                'job_description': '''• 피부팀 관리 및 교육
• 레이저/피부 시술 어시스트
• 시술 프로토콜 관리
• 신입 교육 및 관리
• 고객 사후관리
• 시술실 환경 관리''',
                'working_hours': '평일 09:00-18:00 (점심시간 12:00-13:00)',
                'working_location': '리버스클리닉 홍대점',
                'urgency_level': 'medium'
            },
            {
                'name': '피부팀원 채용 템플릿',
                'description': '리버스클리닉 홍대점 피부팀원 채용용 템플릿',
                'position_title': '피부팀원',
                'department': '피부팀',
                'employment_type': 'full_time',
                'salary_min': 2000,
                'salary_max': 2800,
                'required_experience': '''• 신입/경력 무관
• 인원 제한 없음
• 피부관리 관련 경험 우대
• 레이저 어시스트 경험 우대''',
                'preferred_qualifications': '''• 피부과 관련 전공
• 피부관리사 자격증
• 레이저 시술 보조 경험
• 고객 관리 경험''',
                'job_description': '''• 피부관리(관리실 시술, 레이저 어시 등)
• 고객 관리 및 사후관리
• 시술실 환경 관리
• 피부팀장 보조
• 고객 응대 및 안내''',
                'working_hours': '평일 09:00-18:00 (점심시간 12:00-13:00)',
                'working_location': '리버스클리닉 홍대점',
                'urgency_level': 'low'
            },
            {
                'name': '간호팀장 채용 템플릿',
                'description': '리버스클리닉 홍대점 간호팀장 채용용 템플릿',
                'position_title': '간호팀장',
                'department': '간호팀',
                'employment_type': 'full_time',
                'salary_min': 3200,
                'salary_max': 4000,
                'required_experience': '''• 경력자(팀장급) 우대
• 간호사 면허 소지
• 주사 및 시술 어시스트 경험 5년 이상
• 팀 관리 및 교육 경험
• 신입 교육 및 관리 경험''',
                'preferred_qualifications': '''• 피부과 간호 경험
• 주사 시술 전문 경험
• 팀 리더십 경험
• 의료기기 및 약품 관리 경험''',
                'job_description': '''• 간호팀 관리 및 교육
• 주사, 시술 어시스트
• 의료기기 및 약품 관리
• 신입 교육 및 관리
• 환자 안내 및 진료실 보조
• 시술실 환경 관리''',
                'working_hours': '평일 09:00-18:00 (점심시간 12:00-13:00)',
                'working_location': '리버스클리닉 홍대점',
                'urgency_level': 'medium'
            },
            {
                'name': '간호팀원 채용 템플릿',
                'description': '리버스클리닉 홍대점 간호팀원 채용용 템플릿',
                'position_title': '간호팀원',
                'department': '간호팀',
                'employment_type': 'full_time',
                'salary_min': 2000,
                'salary_max': 2800,
                'required_experience': '''• 신입/경력 무관
• 인원 제한 없음
• 간호사 면허 소지
• 주사/시술 어시스트 경험 우대''',
                'preferred_qualifications': '''• 피부과 간호 경험
• 주사 시술 경험
• 비만/제모 시술 보조 경험
• 환자 안내 경험''',
                'job_description': '''• 주사/시술 어시스트
• 비만/제모 시술 지원
• 환자 안내 및 진료실 보조
• 간호팀장 보조
• 의료기기 및 약품 관리
• 시술실 환경 관리''',
                'working_hours': '평일 09:00-18:00 (점심시간 12:00-13:00)',
                'working_location': '리버스클리닉 홍대점',
                'urgency_level': 'low'
            }
        ]
        
        created_count = 0
        for template_data in templates_data:
            try:
                # 병원 정보 설정
                template_data.update({
                    'hospital_name': hospital_org.name,
                    'hospital_branch': hongdae_branch.name,
                    'hospital_address': hongdae_branch.address,
                    'hospital_phone': hongdae_branch.phone,
                    'hospital_contact_person': hongdae_branch.manager_name,
                })
                
                # 템플릿 생성
                template, created = JobRequestTemplate.objects.get_or_create(
                    name=template_data['name'],
                    defaults={
                        'description': template_data['description'],
                        'created_by': admin_user,
                        'branch': hongdae_branch,
                        'hospital_name': template_data['hospital_name'],
                        'hospital_branch': template_data['hospital_branch'],
                        'hospital_address': template_data['hospital_address'],
                        'hospital_phone': template_data['hospital_phone'],
                        'hospital_contact_person': template_data['hospital_contact_person'],
                        'position_title': template_data['position_title'],
                        'department': template_data['department'],
                        'employment_type': template_data['employment_type'],
                        'salary_min': template_data['salary_min'],
                        'salary_max': template_data['salary_max'],
                        'required_experience': template_data['required_experience'],
                        'preferred_qualifications': template_data['preferred_qualifications'],
                        'job_description': template_data['job_description'],
                        'working_hours': template_data['working_hours'],
                        'working_location': template_data['working_location'],
                        'urgency_level': template_data['urgency_level'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'✓ {template.name} 템플릿을 생성했습니다.')
                else:
                    self.stdout.write(f'- {template.name} 템플릿이 이미 존재합니다.')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'템플릿 생성 중 오류 ({template_data["name"]}): {e}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n채용 요청 템플릿 생성이 완료되었습니다!\n'
                f'• 생성된 템플릿: {created_count}개\n'
                f'• 기관: {hospital_org.name}\n'
                f'• 지점: {hongdae_branch.get_full_name()}\n\n'
                f'생성된 템플릿:\n'
                f'1. 총괄실장 채용 템플릿\n'
                f'2. 상담실장 채용 템플릿\n'
                f'3. 코디네이터 채용 템플릿\n'
                f'4. 피부팀장 채용 템플릿\n'
                f'5. 피부팀원 채용 템플릿\n'
                f'6. 간호팀장 채용 템플릿\n'
                f'7. 간호팀원 채용 템플릿\n\n'
                f'이제 채용 요청 생성 시 이 템플릿들을 선택하여 사용할 수 있습니다.'
            )
        ) 