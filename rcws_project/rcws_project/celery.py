import os
from celery import Celery

# Django 설정 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcws_project.settings')

app = Celery('rcws_project')

# Django 설정에서 Celery 설정 로드
app.config_from_object('django.conf:settings', namespace='CELERY')

# 자동으로 앱에서 tasks.py 파일들을 찾아서 등록
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 