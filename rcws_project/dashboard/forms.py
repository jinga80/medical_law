from django import forms


class DashboardFilterForm(forms.Form):
    """대시보드 필터 폼"""
    
    PERIOD_CHOICES = [
        ('today', '오늘'),
        ('week', '이번 주'),
        ('month', '이번 달'),
        ('quarter', '이번 분기'),
        ('year', '올해')
    ]
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        label='기간',
        initial='month',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    organization = forms.CharField(
        label='조직',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    status = forms.CharField(
        label='상태',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    ) 