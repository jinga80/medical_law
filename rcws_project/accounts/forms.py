from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """사용자 생성 폼"""
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'organization', 'role', 'phone', 
                 'department', 'position', 'employee_id', 'profile_image', 'is_active', 'is_staff', 
                 'is_superuser', 'is_active_user')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class CustomUserChangeForm(UserChangeForm):
    """사용자 수정 폼"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'organization', 'role', 'phone', 
                 'department', 'position', 'employee_id', 'profile_image', 'is_active', 'is_staff', 
                 'is_superuser', 'is_active_user')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    """사용자 프로필 수정 폼"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'position', 
                 'employee_id', 'profile_image']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        } 