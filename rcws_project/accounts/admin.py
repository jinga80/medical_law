from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Organization, UserActivity, Branch, Hospital, HospitalBranch, PositionTemplate
from .forms import UserCreationForm, UserChangeForm


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'org_type', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['org_type', 'is_active', 'created_at']
    search_fields = ['name', 'address', 'phone', 'email']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'org_type', 'description')
        }),
        ('연락처 정보', {
            'fields': ('address', 'phone', 'email')
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'system_admin':
            return qs
        else:
            return qs.filter(users=request.user)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'organization', 'manager_name', 'phone', 'is_active', 'created_at']
    list_filter = ['organization', 'is_active', 'created_at']
    search_fields = ['name', 'address', 'phone', 'manager_name']
    list_editable = ['is_active']
    ordering = ['organization', 'name']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = '전체 지점명'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('organization', 'name', 'description')
        }),
        ('연락처 정보', {
            'fields': ('address', 'phone', 'email')
        }),
        ('지점장 정보', {
            'fields': ('manager_name', 'manager_phone')
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'organization', 'branch', 'is_active', 'is_staff')
    list_filter = ('role', 'organization', 'branch', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('role', 'organization', 'branch', 'phone', 'profile_image')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('추가 정보', {'fields': ('role', 'organization', 'branch', 'phone', 'profile_image')}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'system_admin':
            return qs
        else:
            return qs.filter(organization=request.user.organization)
    
    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser and request.user.role != 'system_admin':
            # 일반 사용자는 제한된 필드만 수정 가능
            return (
                ('기본 정보', {
                    'fields': ('first_name', 'last_name', 'email')
                }),
                ('소속 정보', {
                    'fields': ('role', 'organization', 'branch')
                }),
                ('연락처', {
                    'fields': ('phone',)
                }),
            )
        return super().get_fieldsets(request, obj)
    
    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.role == 'system_admin'
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'system_admin'
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.role == 'system_admin':
            return True
        if obj and obj == request.user:
            return True
        return False


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.role == 'system_admin'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'system_admin':
            return qs
        else:
            return qs.filter(user__organization=request.user.organization)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'phone', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('name', 'organization__name', 'address')
    ordering = ('name',)


@admin.register(HospitalBranch)
class HospitalBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'hospital', 'phone', 'manager_name', 'is_active')
    list_filter = ('hospital', 'is_active')
    search_fields = ('name', 'hospital__name', 'address', 'manager_name')
    ordering = ('hospital', 'name')


@admin.register(PositionTemplate)
class PositionTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'employment_type', 'is_default', 'is_active', 'created_by')
    list_filter = ('department', 'employment_type', 'is_default', 'is_active')
    search_fields = ('name', 'department', 'job_description')
    ordering = ('department', 'name')
