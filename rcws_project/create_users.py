#!/usr/bin/env python
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcws_project.settings')
django.setup()

from accounts.models import User, Organization, Branch
from django.contrib.auth.hashers import make_password

def create_users():
    """새로운 사용자들을 생성합니다."""
    
    # 조직 가져오기
    try:
        admin_org = Organization.objects.filter(org_type='admin').first()
        hospital_org = Organization.objects.filter(org_type='hospital').first()
        headhunting_org = Organization.objects.filter(org_type='headhunting').first()
        
        if not admin_org or not hospital_org or not headhunting_org:
            print("필요한 조직이 존재하지 않습니다.")
            return
    except Exception as e:
        print(f"조직 조회 중 오류 발생: {e}")
        return
    
    # 1. 총 관리자 계정 (admin / 12345)
    admin_user = User.objects.create(
        username='admin',
        email='admin@rcws.com',
        password=make_password('12345'),
        first_name='시스템',
        last_name='관리자',
        organization=admin_org,
        role='system_admin',
        phone='010-0000-0001',
        department='시스템관리팀',
        position='총괄관리자',
        employee_id='ADMIN001',
        is_superuser=True,
        is_staff=True,
        is_active=True
    )
    print(f"✅ 총 관리자 계정 생성 완료: admin / 12345")
    
    # 2. 병원 계정 (reverse / 12345)
    reverse_user = User.objects.create(
        username='reverse',
        email='hr@reverseclinic.com',
        password=make_password('12345'),
        first_name='리버스',
        last_name='클리닉',
        organization=hospital_org,
        role='hospital_hr',
        phone='010-0000-0002',
        department='인사팀',
        position='인사담당자',
        employee_id='HOSP001',
        is_superuser=False,
        is_staff=False,
        is_active=True
    )
    print(f"✅ 병원 계정 생성 완료: reverse / 12345")
    
    # 3. 채용관리업체 계정 (hr1 / 12345)
    hr1_user = User.objects.create(
        username='hr1',
        email='hr@kgoutsourcing.com',
        password=make_password('12345'),
        first_name='케이지',
        last_name='아웃소싱',
        organization=headhunting_org,
        role='hh_manager',
        phone='010-0000-0003',
        department='헤드헌팅팀',
        position='팀장',
        employee_id='HH001',
        is_superuser=False,
        is_staff=False,
        is_active=True
    )
    print(f"✅ 채용관리업체 계정 생성 완료: hr1 / 12345")
    
    print("\n🎉 모든 사용자 생성이 완료되었습니다!")
    print("\n📋 생성된 계정 목록:")
    print("1. 총 관리자: admin / 12345 (시스템 관리자)")
    print("2. 병원: reverse / 12345 (병원 인사담당자)")
    print("3. 채용관리업체: hr1 / 12345 (헤드헌팅 팀장)")
    
    # 사용자 권한 확인
    print("\n🔐 권한 확인:")
    print(f"admin (총 관리자): superuser={admin_user.is_superuser}, staff={admin_user.is_staff}")
    print(f"reverse (병원): role={reverse_user.get_role_display()}")
    print(f"hr1 (채용관리업체): role={hr1_user.get_role_display()}")

if __name__ == '__main__':
    create_users() 