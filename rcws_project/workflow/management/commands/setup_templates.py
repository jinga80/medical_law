from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from workflow.models import JobRequestTemplate

User = get_user_model()

class Command(BaseCommand):
    help = '기본 채용 요청 템플릿을 생성합니다.'

    def handle(self, *args, **options):
        # 관리자 사용자 찾기
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('관리자 사용자가 없습니다. 먼저 관리자를 생성해주세요.')
            )
            return

        # 기존 템플릿이 있는지 확인
        if JobRequestTemplate.objects.exists():
            self.stdout.write(
                self.style.WARNING('이미 템플릿이 존재합니다. 기존 템플릿을 유지합니다.')
            )
            return

        # 기본 템플릿들 생성
        templates_data = [
            {
                'name': '일반 간호사 채용',
                'description': '일반적인 간호사 채용을 위한 기본 템플릿입니다.',
                'is_default': True,
                'position_title': '간호사',
                'department': '간호부',
                'employment_type': 'full_time',
                'salary_min': 3000,
                'salary_max': 4500,
                'required_experience': '간호사 면허 소지자\n신규 간호사 또는 경력 간호사\n근무 가능한 자',
                'preferred_qualifications': '3년 이상 경력자 우대\n특정 진료과 경험자 우대\n야간 근무 가능자 우대',
                'job_description': '환자 간호 및 치료 보조\n의료진과의 협력\n환자 상태 관찰 및 기록\n투약 및 처치 보조',
                'working_hours': '주 5일 근무, 8시간/일',
                'working_location': '병원 내',
                'urgency_level': 'medium',
            },
            {
                'name': '전문 간호사 채용',
                'description': '전문 간호사 채용을 위한 템플릿입니다.',
                'is_default': False,
                'position_title': '전문 간호사',
                'department': '간호부',
                'employment_type': 'full_time',
                'salary_min': 4000,
                'salary_max': 6000,
                'required_experience': '전문 간호사 자격증 소지자\n5년 이상 임상 경력\n전문 분야별 경험',
                'preferred_qualifications': '대학원 졸업자 우대\n연구 경험자 우대\n교육 경험자 우대',
                'job_description': '전문 분야별 고급 간호 제공\n간호 교육 및 지도\n간호 연구 및 품질 관리\n의료진과의 협력',
                'working_hours': '주 5일 근무, 8시간/일',
                'working_location': '병원 내',
                'urgency_level': 'high',
            },
            {
                'name': '의료진 채용',
                'description': '의사, 약사 등 의료진 채용을 위한 템플릿입니다.',
                'is_default': False,
                'position_title': '전문의',
                'department': '내과',
                'employment_type': 'full_time',
                'salary_min': 8000,
                'salary_max': 12000,
                'required_experience': '의사 면허 소지자\n전문의 자격증 소지자\n해당 진료과 경험',
                'preferred_qualifications': '대학병원 경험자 우대\n연구 실적 보유자 우대\n교육 경험자 우대',
                'job_description': '환자 진료 및 치료\n의료진 교육 및 지도\n의료 연구 및 학술 활동\n병원 행정 참여',
                'working_hours': '주 5일 근무, 8시간/일',
                'working_location': '병원 내',
                'urgency_level': 'high',
            },
            {
                'name': '행정직 채용',
                'description': '병원 행정직 채용을 위한 템플릿입니다.',
                'is_default': False,
                'position_title': '행정직원',
                'department': '행정과',
                'employment_type': 'full_time',
                'salary_min': 2500,
                'salary_max': 3500,
                'required_experience': '대학 졸업자\n컴퓨터 활용 능력\n고객 응대 경험',
                'preferred_qualifications': '병원 행정 경험자 우대\n의료정보관리사 자격증 소지자 우대\n외국어 능력자 우대',
                'job_description': '환자 접수 및 안내\n의료비 계산 및 수납\n행정 업무 보조\n고객 응대',
                'working_hours': '주 5일 근무, 8시간/일',
                'working_location': '병원 내',
                'urgency_level': 'low',
            },
            {
                'name': '계약직 채용',
                'description': '계약직 채용을 위한 템플릿입니다.',
                'is_default': False,
                'position_title': '계약직 간호사',
                'department': '간호부',
                'employment_type': 'contract',
                'salary_min': 2800,
                'salary_max': 3500,
                'required_experience': '간호사 면허 소지자\n근무 가능한 자',
                'preferred_qualifications': '해당 진료과 경험자 우대\n야간 근무 가능자 우대',
                'job_description': '환자 간호 및 치료 보조\n의료진과의 협력\n환자 상태 관찰 및 기록',
                'working_hours': '계약에 따른 근무',
                'working_location': '병원 내',
                'urgency_level': 'medium',
            },
        ]

        created_count = 0
        for template_data in templates_data:
            template = JobRequestTemplate.objects.create(
                created_by=admin_user,
                **template_data
            )
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'템플릿 생성: {template.name}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'총 {created_count}개의 기본 템플릿이 생성되었습니다.')
        ) 