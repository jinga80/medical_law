from django import forms
from .models import Notification


class NotificationForm(forms.ModelForm):
    """알림 폼"""
    
    class Meta:
        model = Notification
        fields = ['recipient', 'title', 'message', 'notification_type', 'related_object_type', 'related_object_id']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'related_object_type': forms.TextInput(attrs={'class': 'form-control'}),
            'related_object_id': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 필수 필드 표시
        for field_name in ['recipient', 'title', 'message']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required' 