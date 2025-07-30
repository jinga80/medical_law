from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Organization

User = get_user_model()


class Command(BaseCommand):
    help = '초기 사용자들을 생성합니다.'

    def handle(self, *args, **options):
        self.stdout.write('초기 사용자 생성을 시작합니다...')
        
        # 1. 기관 생성
        self.create_organizations()
        
        # 2. 사용자 생성
        self.create_users()
        
        self.stdout.write(
            self.style.SUCCESS('초기 사용자 생성이 완료되었습니다!')
        )

    def create_organizations(self):
        """기관 생성"""
        # 메디킹 관리기관
        admin_org, created = Organization.objects.get_or_create(
            name='메디킹 관리기관',
            defaults={
                'org_type': 'admin',
                'address': '서울특별시 강남구',
                'phone': '02-1234-5678',
                'email': 'admin@mediking.com',
                'description': 'RCWS 시스템 관리기관'
            }
        )
        if created:
            self.stdout.write(f'기관 생성: {admin_org.name}')
        
        # 리버스클리닉 (병원)
        hospital_org, created = Organization.objects.get_or_create(
            name='리버스클리닉',
            defaults={
                'org_type': 'hospital',
                'address': '서울특별시 서초구',
                'phone': '02-2345-6789',
                'email': 'hr@reverseclinic.com',
                'description': '리버스클리닉 병원'
            }
        )
        if created:
            self.stdout.write(f'기관 생성: {hospital_org.name}')
        
        # 케이지아웃소싱 (헤드헌팅)
        headhunting_org, created = Organization.objects.get_or_create(
            name='케이지아웃소싱',
            defaults={
                'org_type': 'headhunting',
                'address': '서울특별시 마포구',
                'phone': '02-3456-7890',
                'email': 'hr@kgoutsourcing.com',
                'description': '케이지아웃소싱 헤드헌팅'
            }
        )
        if created:
            self.stdout.write(f'기관 생성: {headhunting_org.name}')

    def create_users(self):
        """사용자 생성"""
        # 메디킹 관리자 (mediking)
        mediking_user, created = User.objects.get_or_create(
            username='mediking',
            defaults={
                'first_name': '메디킹',
                'last_name': '관리자',
                'email': 'admin@mediking.com',
                'organization': Organization.objects.get(name='메디킹 관리기관'),
                'role': 'system_admin',
                'department': '시스템관리팀',
                'position': '시스템 관리자',
                'employee_id': 'ADMIN001',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        if created:
            mediking_user.set_password('1234')
            mediking_user.save()
            self.stdout.write(f'사용자 생성: {mediking_user.username} (비밀번호: 1234)')
        
        # 병원 관계자들
        hospital_users = [
            {
                'username': 'hospital_admin1',
                'first_name': '병원',
                'last_name': '관리자1',
                'email': 'admin1@reverseclinic.com',
                'role': 'hospital_manager',
                'department': '인사팀',
                'position': '팀장',
                'employee_id': 'HOSP001'
            },
            {
                'username': 'hospital_hr1',
                'first_name': '병원',
                'last_name': '인사담당자1',
                'email': 'hr1@reverseclinic.com',
                'role': 'hospital_hr',
                'department': '인사팀',
                'position': '대리',
                'employee_id': 'HOSP002'
            },
            {
                'username': 'hospital_hr2',
                'first_name': '병원',
                'last_name': '인사담당자2',
                'email': 'hr2@reverseclinic.com',
                'role': 'hospital_hr',
                'department': '인사팀',
                'position': '사원',
                'employee_id': 'HOSP003'
            }
        ]
        
        hospital_org = Organization.objects.get(name='리버스클리닉')
        for user_data in hospital_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                    'organization': hospital_org,
                    'role': user_data['role'],
                    'department': user_data['department'],
                    'position': user_data['position'],
                    'employee_id': user_data['employee_id'],
                    'is_active': True
                }
            )
            if created:
                user.set_password('1234')
                user.save()
                self.stdout.write(f'사용자 생성: {user.username} (비밀번호: 1234)')
        
        # 헤드헌팅 담당자들
        headhunting_users = [
            {
                'username': 'hh_admin1',
                'first_name': '헤드헌팅',
                'last_name': '관리자1',
                'email': 'admin1@kgoutsourcing.com',
                'role': 'hh_ceo',
                'department': '경영팀',
                'position': '대표',
                'employee_id': 'HH001'
            },
            {
                'username': 'hh_manager1',
                'first_name': '헤드헌팅',
                'last_name': '담당자1',
                'email': 'manager1@kgoutsourcing.com',
                'role': 'hh_manager',
                'department': '채용팀',
                'position': '팀장',
                'employee_id': 'HH002'
            },
            {
                'username': 'hh_staff1',
                'first_name': '헤드헌팅',
                'last_name': '담당자2',
                'email': 'staff1@kgoutsourcing.com',
                'role': 'hh_staff',
                'department': '채용팀',
                'position': '대리',
                'employee_id': 'HH003'
            }
        ]
        
        headhunting_org = Organization.objects.get(name='케이지아웃소싱')
        for user_data in headhunting_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': user_data['email'],
                    'organization': headhunting_org,
                    'role': user_data['role'],
                    'department': user_data['department'],
                    'position': user_data['position'],
                    'employee_id': user_data['employee_id'],
                    'is_active': True
                }
            )
            if created:
                user.set_password('1234')
                user.save()
                self.stdout.write(f'사용자 생성: {user.username} (비밀번호: 1234)')
        
        self.stdout.write('\n=== 생성된 사용자 목록 ===')
        self.stdout.write('메디킹 관리자: mediking / 1234')
        self.stdout.write('병원 관계자: hospital_admin1, hospital_hr1, hospital_hr2 / 1234')
        self.stdout.write('헤드헌팅 담당자: hh_admin1, hh_manager1, hh_staff1 / 1234')
        self.stdout.write('\n모든 사용자의 기본 비밀번호는 1234입니다.') 