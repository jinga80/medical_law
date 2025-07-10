from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def status_display(status_value):
    """상태값을 사람이 읽기 쉬운 형태로 변환"""
    status_choices = {
        'pending': '대기중',
        'in_progress': '진행중',
        'completed': '완료',
        'cancelled': '취소',
        'on_hold': '보류',
        'draft': '작성중',
        'submitted': '제출완료',
        'accepted': '접수완료',
        'published': '게시중',
        'paused': '일시중지',
        'closed': '마감',
        'expired': '만료',
        'recommended': '추천 대기',
        'document_review': '서류 검토',
        'interview_scheduled': '면접 예정',
        'interviewed': '면접 완료',
        'hired': '채용 확정',
        'rejected': '불합격',
        'withdrawn': '지원철회',
        'under_review': '검토중',
        'shortlisted': '서류합격',
    }
    return status_choices.get(status_value, status_value)

@register.filter
def status_color(status):
    """상태에 따른 색상 반환"""
    color_map = {
        'pending': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'cancelled': 'danger',
        'on_hold': 'warning',
        'draft': 'secondary',
        'submitted': 'info',
        'accepted': 'primary',
        'in_progress': 'warning',
        'completed': 'success',
        'cancelled': 'danger',
        'on_hold': 'warning',
        'published': 'success',
        'paused': 'warning',
        'closed': 'danger',
        'expired': 'dark',
        'submitted': 'secondary',
        'under_review': 'warning',
        'shortlisted': 'success',
        'rejected': 'danger',
        'withdrawn': 'dark',
    }
    return color_map.get(status, 'secondary')

@register.filter
def status_icon(status):
    """상태에 따른 아이콘 반환"""
    icon_map = {
        'pending': 'mdi-clock',
        'in_progress': 'mdi-play-circle',
        'completed': 'mdi-check-circle',
        'cancelled': 'mdi-close-circle',
        'on_hold': 'mdi-pause-circle',
        'draft': 'mdi-file-document-outline',
        'submitted': 'mdi-send',
        'accepted': 'mdi-check',
        'published': 'mdi-publish',
        'paused': 'mdi-pause',
        'closed': 'mdi-close',
        'expired': 'mdi-alert',
        'under_review': 'mdi-eye',
        'shortlisted': 'mdi-star',
        'rejected': 'mdi-close',
        'withdrawn': 'mdi-undo',
    }
    return icon_map.get(status, 'mdi-help-circle')

@register.filter
def progress_color(progress):
    """진행률에 따른 색상 반환"""
    if progress >= 80:
        return 'success'
    elif progress >= 60:
        return 'info'
    elif progress >= 40:
        return 'warning'
    else:
        return 'danger'

@register.filter
def urgency_color(urgency):
    """긴급도에 따른 색상 반환"""
    color_map = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
    }
    return color_map.get(urgency, 'secondary')

@register.simple_tag
def workflow_progress_bar(progress, width="100%"):
    """워크플로우 진행률 바 HTML 생성"""
    color = progress_color(progress)
    html = f'''
    <div class="progress" style="height: 8px;">
        <div class="progress-bar bg-{color}" role="progressbar" 
             style="width: {progress}%;" 
             aria-valuenow="{progress}" 
             aria-valuemin="0" 
             aria-valuemax="100">
        </div>
    </div>
    <small class="text-muted mt-1 d-block">{progress}% 완료</small>
    '''
    return mark_safe(html)

@register.filter
def action_color(action_type):
    """액션 타입에 따른 색상 반환"""
    color_map = {
        'status_change': 'primary',
        'status_revert': 'warning',
        'step_complete': 'success',
        'step_revert': 'warning',
        'note_add': 'info',
        'note_edit': 'info',
        'assignment_change': 'secondary',
        'due_date_change': 'secondary',
        'workflow_create': 'success',
        'workflow_edit': 'primary',
        'workflow_delete': 'danger',
        'step_create': 'success',
        'step_edit': 'primary',
        'step_delete': 'danger',
    }
    return color_map.get(action_type, 'secondary')

@register.filter
def action_icon(action_type):
    """액션 타입에 따른 아이콘 반환"""
    icon_map = {
        'status_change': 'fas fa-exchange-alt',
        'status_revert': 'fas fa-undo',
        'step_complete': 'fas fa-check-circle',
        'step_revert': 'fas fa-undo',
        'note_add': 'fas fa-sticky-note',
        'note_edit': 'fas fa-edit',
        'assignment_change': 'fas fa-user-edit',
        'due_date_change': 'fas fa-calendar-alt',
        'workflow_create': 'fas fa-plus-circle',
        'workflow_edit': 'fas fa-edit',
        'workflow_delete': 'fas fa-trash',
        'step_create': 'fas fa-plus',
        'step_edit': 'fas fa-edit',
        'step_delete': 'fas fa-trash',
    }
    return icon_map.get(action_type, 'fas fa-info-circle')

@register.filter
def get_item(dictionary, key):
    """딕셔너리에서 키로 값을 가져오는 필터"""
    return dictionary.get(key)

@register.filter
def get_status_color(status):
    """상태에 따른 색상 반환"""
    color_map = {
        'draft': 'secondary',
        'submitted': 'info',
        'accepted': 'primary',
        'in_progress': 'warning',
        'completed': 'success',
        'cancelled': 'danger',
        'waiting': 'secondary',
        'under_review': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'interview_scheduled': 'info',
        'interviewed': 'primary',
        'hired': 'success',
        'final_approved': 'success',
        'final_rejected': 'danger',
    }
    return color_map.get(status, 'secondary')

@register.filter
def get_status_display(status):
    """상태 표시명 반환"""
    display_map = {
        'draft': '작성중',
        'submitted': '제출완료',
        'accepted': '승인됨',
        'in_progress': '진행중',
        'completed': '완료',
        'cancelled': '취소됨',
        'waiting': '대기중',
        'under_review': '검토중',
        'approved': '승인됨',
        'rejected': '거절됨',
        'interview_scheduled': '면접예정',
        'interviewed': '면접완료',
        'hired': '채용됨',
        'final_approved': '최종승인',
        'final_rejected': '최종거절',
    }
    return display_map.get(status, status)

@register.filter
def get_position_display(position):
    """직책 표시명 반환"""
    display_map = {
        'doctor': '의사',
        'nurse': '간호사',
        'pharmacist': '약사',
        'technician': '기술사',
        'administrator': '행정직',
        'other': '기타',
    }
    return display_map.get(position, position)

@register.filter
def get_org_type_display(org_type):
    """기관 유형 표시명 반환"""
    display_map = {
        'hospital': '병원',
        'clinic': '의원',
        'headhunting': '헤드헌팅',
        'admin': '관리자',
    }
    return display_map.get(org_type, org_type) 