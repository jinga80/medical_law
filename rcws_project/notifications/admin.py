from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    NotificationLog, ChatRoom, ChatRoomParticipant, ChatMessage,
    NotificationGroup, NotificationAnalytics
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'notification_type', 'title', 'priority', 
        'is_read', 'created_at', 'organization'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'created_at', 
        'organization', 'recipient'
    ]
    search_fields = ['title', 'message', 'recipient__username', 'recipient__first_name']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('recipient', 'organization', 'notification_type', 'title', 'message')
        }),
        ('우선순위 및 액션', {
            'fields': ('priority', 'action_required', 'action_url', 'action_text')
        }),
        ('관련 객체', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('상태 및 시간', {
            'fields': ('is_read', 'read_at', 'created_at', 'scheduled_at', 'sent_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated}개의 알림을 읽음으로 표시했습니다.')
    mark_as_read.short_description = "선택된 알림을 읽음으로 표시"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated}개의 알림을 읽지 않음으로 표시했습니다.')
    mark_as_unread.short_description = "선택된 알림을 읽지 않음으로 표시"


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'is_active', 'created_at']
    list_filter = ['notification_type', 'is_active', 'created_at']
    search_fields = ['name', 'title_template', 'message_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'notification_type', 'is_active')
        }),
        ('템플릿 내용', {
            'fields': ('title_template', 'message_template', 'variables_description')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_notifications', 'web_notifications', 'sms_notifications', 'updated_at']
    list_filter = ['email_notifications', 'web_notifications', 'sms_notifications', 'updated_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('사용자 정보', {
            'fields': ('user',)
        }),
        ('알림 방법', {
            'fields': ('email_notifications', 'web_notifications', 'sms_notifications')
        }),
        ('알림 유형별 설정', {
            'fields': (
                'job_request_notifications', 'candidate_notifications', 
                'interview_notifications', 'workflow_notifications', 'system_notifications'
            )
        }),
        ('시간 설정', {
            'fields': ('quiet_hours_start', 'quiet_hours_end'),
            'classes': ('collapse',)
        }),
        ('메타 정보', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'notification', 'delivery_method', 'status', 'sent_at', 'delivered_at'
    ]
    list_filter = ['delivery_method', 'status', 'sent_at']
    search_fields = ['notification__title', 'notification__recipient__username']
    readonly_fields = ['sent_at', 'delivered_at']
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('notification', 'delivery_method', 'status')
        }),
        ('시간 정보', {
            'fields': ('sent_at', 'delivered_at')
        }),
        ('오류 정보', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'room_type', 'created_by', 'get_participant_count', 
        'is_active', 'is_private', 'created_at'
    ]
    list_filter = ['room_type', 'is_active', 'is_private', 'created_at']
    search_fields = ['name', 'created_by__username', 'created_by__first_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'room_type', 'created_by')
        }),
        ('관련 객체', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('설정', {
            'fields': ('is_active', 'is_private', 'max_participants')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_participant_count(self, obj):
        return obj.get_participant_count()
    get_participant_count.short_description = '참여자 수'


@admin.register(ChatRoomParticipant)
class ChatRoomParticipantAdmin(admin.ModelAdmin):
    list_display = ['chat_room', 'user', 'role', 'joined_at', 'is_active']
    list_filter = ['role', 'is_active', 'joined_at', 'chat_room__room_type']
    search_fields = ['user__username', 'user__first_name', 'chat_room__name']
    readonly_fields = ['joined_at']
    
    fieldsets = (
        ('참여자 정보', {
            'fields': ('chat_room', 'user', 'role')
        }),
        ('참여 정보', {
            'fields': ('joined_at', 'last_read_at', 'is_active')
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'chat_room', 'sender', 'message_type', 'get_content_preview', 
        'is_edited', 'is_deleted', 'created_at'
    ]
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'created_at', 'chat_room__room_type']
    search_fields = ['content', 'sender__username', 'sender__first_name', 'chat_room__name']
    readonly_fields = ['created_at', 'edited_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('chat_room', 'sender', 'message_type')
        }),
        ('메시지 내용', {
            'fields': ('content', 'file_url', 'file_name', 'file_size')
        }),
        ('상태', {
            'fields': ('is_edited', 'is_deleted', 'edited_at')
        }),
        ('메타 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    get_content_preview.short_description = '내용 미리보기'


@admin.register(NotificationGroup)
class NotificationGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_member_count', 'is_active', 'auto_add_new_users', 'created_at']
    list_filter = ['is_active', 'auto_add_new_users', 'priority_filter', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['members']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'description')
        }),
        ('멤버 관리', {
            'fields': ('members', 'auto_add_new_users')
        }),
        ('설정', {
            'fields': ('is_active', 'notification_types', 'priority_filter')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member_count(self, obj):
        return obj.get_member_count()
    get_member_count.short_description = '멤버 수'


@admin.register(NotificationAnalytics)
class NotificationAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'date', 'total_notifications', 'read_notifications', 
        'unread_notifications', 'get_read_rate', 'avg_response_time_minutes'
    ]
    list_filter = ['date', 'organization', 'created_at']
    search_fields = ['organization__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('date', 'organization')
        }),
        ('알림 통계', {
            'fields': ('total_notifications', 'read_notifications', 'unread_notifications')
        }),
        ('상세 통계', {
            'fields': ('notification_type_counts', 'priority_counts', 'delivery_method_counts'),
            'classes': ('collapse',)
        }),
        ('응답 시간', {
            'fields': ('avg_response_time_minutes',),
            'classes': ('collapse',)
        }),
        ('메타 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_read_rate(self, obj):
        return f"{obj.get_read_rate():.1f}%"
    get_read_rate.short_description = '읽음률'
