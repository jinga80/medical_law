from django import template
import re

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """딕셔너리에서 키로 값을 가져오는 필터"""
    return dictionary.get(key)

@register.filter
def highlight_violations(text, violations):
    """
    위반 키워드가 등장한 부분을 <mark> 태그로 하이라이트합니다.
    여러 키워드가 있을 경우 모두 강조합니다.
    """
    if not violations:
        return text
    # 중복 방지 및 긴 키워드 우선
    keywords = sorted(set(v['keyword'] for v in violations if v.get('keyword')), key=lambda k: -len(k))
    if not keywords:
        return text
    # 정규식 패턴 생성 (중복 방지)
    pattern = re.compile(r'(' + '|'.join(map(re.escape, keywords)) + r')', re.IGNORECASE)
    return pattern.sub(r'<mark style="background: #fef08a; color: #b45309; font-weight: bold;">\1</mark>', text) 