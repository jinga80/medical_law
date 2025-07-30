import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Avg
from django.core.paginator import Paginator
from .models import (
    ComplianceAnalysis, MedicalGuideline, ComplianceRule, MedicalLawInfo,
    GuidelineDocument, GuidelineUpdate, AIAnalysisResult, ComplianceCategory
)
from .utils import TextExtractor, WebTextExtractor, extract_text_from_file
from .analyzer import ComplianceAnalyzer
import logging
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import os
from anthropic import Anthropic
from typing import List, Dict

# Claude API 설정 - .env 파일 또는 시스템 환경변수에서 로드
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# import openai  # 실제 OpenAI API 사용 시 주석 해제

logger = logging.getLogger(__name__)

def index(request):
    """메인 페이지"""
    try:
        return render(request, 'compliance_checker/index.html')
    except Exception as e:
        # 오류 발생 시 간단한 응답 반환
        return HttpResponse(f"<h1>의료광고법 준수 검토 시스템</h1><p>시스템이 정상적으로 작동 중입니다.</p><p>오류: {str(e)}</p>")

def test_view(request):
    """테스트 페이지 - 간단한 응답"""
    return HttpResponse("<h1>테스트 성공!</h1><p>Django가 정상적으로 작동 중입니다.</p>")

def health_check(request):
    """헬스체크 엔드포인트"""
    from django.conf import settings
    return JsonResponse({
        'status': 'healthy',
        'message': '서버가 정상 작동 중입니다',
        'timestamp': timezone.now().isoformat(),
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'host_header': request.META.get('HTTP_HOST', 'None')
    })

def dashboard(request):
    """대시보드 페이지"""
    # 최근 30일 통계
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # 분석 통계
    total_analyses = ComplianceAnalysis.objects.count()
    recent_analyses = ComplianceAnalysis.objects.filter(created_at__gte=thirty_days_ago).count()
    avg_score = ComplianceAnalysis.objects.aggregate(avg_score=Avg('overall_score'))['avg_score'] or 0
    
    # 위험도별 통계
    risk_stats = ComplianceAnalysis.objects.values('risk_level').annotate(count=Count('id'))
    
    # 최근 분석 결과
    recent_results = ComplianceAnalysis.objects.order_by('-created_at')[:10]
    
    # 가이드라인 통계
    total_guidelines = MedicalGuideline.objects.filter(is_active=True).count()
    
    context = {
        'total_analyses': total_analyses,
        'recent_analyses': recent_analyses,
        'avg_score': round(avg_score, 1),
        'risk_stats': list(risk_stats),
        'recent_results': recent_results,
        'total_guidelines': total_guidelines,
    }
    
    return render(request, 'compliance_checker/dashboard.html', context)

def history(request):
    """분석 히스토리 페이지"""
    analyses = ComplianceAnalysis.objects.order_by('-created_at')
    
    # 필터링
    status_filter = request.GET.get('status', '')
    risk_filter = request.GET.get('risk', '')
    type_filter = request.GET.get('type', '')
    date_filter = request.GET.get('date', '')
    search = request.GET.get('search', '')
    
    if status_filter:
        analyses = analyses.filter(compliance_status=status_filter)
    if risk_filter:
        analyses = analyses.filter(risk_level=risk_filter)
    if type_filter:
        analyses = analyses.filter(input_type=type_filter)
    if date_filter:
        if date_filter == 'today':
            analyses = analyses.filter(created_at__date=timezone.now().date())
        elif date_filter == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            analyses = analyses.filter(created_at__gte=week_ago)
        elif date_filter == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            analyses = analyses.filter(created_at__gte=month_ago)
        elif date_filter == 'quarter':
            quarter_ago = timezone.now() - timedelta(days=90)
            analyses = analyses.filter(created_at__gte=quarter_ago)
    if search:
        analyses = analyses.filter(input_text__icontains=search)
    
    # 각 분석에 AI 개선 방안 정보 추가
    for analysis in analyses:
        analysis.has_ai_improvements = False
        if analysis.violations:
            for violation in analysis.violations:
                if isinstance(violation, dict) and 'ai_improvements' in violation and violation['ai_improvements']:
                    analysis.has_ai_improvements = True
                    break
    
    # 통계
    total_count = analyses.count()
    compliant_count = analyses.filter(compliance_status='적합').count()
    partial_count = analyses.filter(compliance_status='부분적합').count()
    non_compliant_count = analyses.filter(compliance_status='부적합').count()
    
    # 페이지네이션
    paginator = Paginator(analyses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'analyses': page_obj,
        'total_count': total_count,
        'compliant_count': compliant_count,
        'partial_count': partial_count,
        'non_compliant_count': non_compliant_count,
    }
    
    return render(request, 'compliance_checker/history.html', context)

def guidelines(request):
    """가이드라인 관리 페이지"""
    guidelines = MedicalGuideline.objects.order_by('-uploaded_at')
    
    # 페이지네이션
    paginator = Paginator(guidelines, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'guidelines': page_obj,
    }
    
    return render(request, 'compliance_checker/guidelines.html', context)

def medical_law_info(request):
    """의료법 정보 페이지"""
    # 의료법 정보 카테고리
    medical_law_categories = {
        'medical_doctors': '의사협회',
        'dental_doctors': '치과협회'
    }
    
    # 의료광고법 카테고리
    advertising_law_categories = {
        'media_types': '심의대상 매체',
        'excluded_items': '심의 제외 대상',
        'general_rules': '일반 규정'
    }
    
    # 심의절차 카테고리
    review_process_categories = {
        'medical_process': '의사협회 심의절차',
        'dental_process': '치과협회 심의절차',
        'general_process': '일반 심의절차'
    }
    
    # 전체 카테고리
    categories = {
        'medical_law': '의료법',
        'advertising_law': '의료광고법', 
        'guidelines': '대한의사협회 가이드라인',
        'notices': '공지사항',
        'penalties': '처벌 기준',
        'review_process': '심의절차',
        'dental_guidelines': '치과의사협회 가이드라인'
    }
    
    law_infos = {}
    for category, display_name in categories.items():
        law_infos[display_name] = MedicalLawInfo.objects.filter(
            category=category, 
            is_active=True
        ).order_by('order', 'title')
    
    return render(request, 'compliance_checker/medical_law_info.html', {
        'law_infos': law_infos,
        'categories': categories,
        'medical_law_categories': medical_law_categories,
        'advertising_law_categories': advertising_law_categories,
        'review_process_categories': review_process_categories
    })

def advertising_law_info(request):
    """의료광고법 정보 페이지"""
    categories = {
        'advertising_law': '의료광고법'
    }
    
    law_infos = {}
    for category, display_name in categories.items():
        law_infos[display_name] = MedicalLawInfo.objects.filter(
            category=category, 
            is_active=True
        ).order_by('order', 'title')
    
    return render(request, 'compliance_checker/advertising_law_info.html', {
        'law_infos': law_infos
    })

def review_process_info(request):
    """심의절차 정보 페이지"""
    categories = {
        'review_process': '심의절차'
    }
    
    law_infos = {}
    for category, display_name in categories.items():
        law_infos[display_name] = MedicalLawInfo.objects.filter(
            category=category, 
            is_active=True
        ).order_by('order', 'title')
    
    return render(request, 'compliance_checker/review_process_info.html', {
        'law_infos': law_infos
    })

@csrf_exempt
@require_http_methods(["POST"])
def analyze_text(request):
    """텍스트 분석 API"""
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        
        if not text:
            return JsonResponse({
                'error': '텍스트를 입력해주세요.'
            }, status=400)
        
        # 분석 실행
        analyzer = ComplianceAnalyzer()
        result = analyzer.analyze_text(text, 'text')
        
        # 결과 저장
        analysis = ComplianceAnalysis.objects.create(
            input_text=text,
            input_type='text',
            overall_score=result['overall_score'],
            compliance_status=result['compliance_status'],
            risk_level=result['risk_level'],
            violations=result['violations'],
            recommendations=result['recommendations']
        )
        
        return JsonResponse({
            'success': True,
            'analysis_id': analysis.id,
            'result': result
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def analyze_file(request):
    """파일 분석 API"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'error': '파일을 업로드해주세요.'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # 파일 텍스트 추출
        try:
            text = extract_text_from_file(uploaded_file)
        except Exception as e:
            return JsonResponse({
                'error': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
            }, status=400)
        
        if not text.strip():
            return JsonResponse({
                'error': '파일에서 텍스트를 추출할 수 없습니다.'
            }, status=400)
        
        # 분석 실행
        analyzer = ComplianceAnalyzer()
        result = analyzer.analyze_text(text, 'file')
        
        # 결과 저장
        analysis = ComplianceAnalysis.objects.create(
            input_text=text,  # 전체 텍스트 저장 (1000자 제한 제거)
            input_type='file',
            file_name=uploaded_file.name,
            overall_score=result['overall_score'],
            compliance_status=result['compliance_status'],
            risk_level=result['risk_level'],
            violations=result['violations'],
            recommendations=result['recommendations']
        )
        
        return JsonResponse({
            'success': True,
            'analysis_id': analysis.id,
            'result': result
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def analyze_url(request):
    """URL 분석 API"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        simple_mode = data.get('simple_mode', False)
        
        if not url:
            return JsonResponse({
                'error': 'URL을 입력해주세요.'
            }, status=400)
        
        # URL에서 텍스트 추출 (개선된 스크래핑)
        try:
            text = WebTextExtractor.extract_from_url(url, simple_mode=simple_mode)
            
            if not text:
                return JsonResponse({
                    'error': '웹페이지에서 텍스트를 추출할 수 없습니다. 다른 URL을 시도해보세요.'
                }, status=400)
            
            # 텍스트 정리
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text.strip()) < 10:
                return JsonResponse({
                    'error': '웹페이지에서 의미있는 텍스트를 추출할 수 없습니다. 다른 URL을 시도해보세요.'
                }, status=400)
            
        except Exception as e:
            logger.error(f"URL 텍스트 추출 실패: {url} - {e}")
            return JsonResponse({
                'error': f'URL에서 텍스트를 추출할 수 없습니다: {str(e)}'
            }, status=400)
        
        # 분석 실행
        analyzer = ComplianceAnalyzer()
        result = analyzer.analyze_text(text, 'url')
        
        # 결과 저장
        analysis = ComplianceAnalysis.objects.create(
            input_text=text,  # 전체 텍스트 저장 (1000자 제한 제거)
            input_type='url',
            url=url,
            overall_score=result['overall_score'],
            compliance_status=result['compliance_status'],
            risk_level=result['risk_level'],
            violations=result['violations'],
            recommendations=result['recommendations']
        )
        
        return JsonResponse({
            'success': True,
            'analysis_id': analysis.id,
            'result': result
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def show_result(request, analysis_id):
    """분석 결과 페이지"""
    try:
        analysis = ComplianceAnalysis.objects.get(id=analysis_id)
        
        # 분석 결과 데이터 가져오기
        if hasattr(analysis, 'analysis_result') and analysis.analysis_result:
            result = analysis.analysis_result
        else:
            # 기존 데이터 구조로부터 결과 재구성
            result = {
                'overall_score': analysis.overall_score,
                'compliance_status': analysis.compliance_status,
                'risk_level': analysis.risk_level,
                'violations': analysis.violations or [],
                'recommendations': analysis.recommendations or [],
                'detailed_violations': getattr(analysis, 'detailed_violations', []),
                'compliance_checklist': getattr(analysis, 'compliance_checklist', []),
                'review_guidance': getattr(analysis, 'review_guidance', {}),
                'extracted_text': analysis.input_text, # 전체 텍스트로 설정
                'text_analysis': {
                    'total_characters': len(analysis.input_text),
                    'total_words': len(analysis.input_text.split()),
                    'total_sentences': len(analysis.input_text.split('.')),
                    'text_quality': 'medium'
                },
                'legal_analysis': {
                    'applicable_laws': [],
                    'legal_risks': [],
                    'compliance_requirements': []
                },
                'summary_report': {
                    'executive_summary': {
                        'total_violations': len(analysis.violations or []),
                        'high_severity': 0,
                        'medium_severity': 0,
                        'low_severity': 0,
                        'compliance_score': analysis.overall_score,
                        'risk_assessment': analysis.risk_level
                    },
                    'key_findings': [],
                    'immediate_actions': [],
                    'long_term_recommendations': []
                }
            }
        
        return render(request, 'compliance_checker/result.html', {
            'result': result,
            'analysis': analysis
        })
        
    except ComplianceAnalysis.DoesNotExist:
        return render(request, 'compliance_checker/result.html', {
            'error': '분석 결과를 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"분석 결과 페이지 오류: {e}")
        return render(request, 'compliance_checker/result.html', {
            'error': '결과를 불러오는 중 오류가 발생했습니다.'
        })

@require_http_methods(["GET"])
def get_analysis_result(request, analysis_id):
    """분석 결과 조회 API"""
    try:
        analysis = ComplianceAnalysis.objects.get(id=analysis_id)
        
        # AI 개선 방안이 있는지 확인
        ai_improvements = []
        if hasattr(analysis, 'ai_improvements') and analysis.ai_improvements:
            ai_improvements = analysis.ai_improvements
        elif 'ai_improvements' in analysis.violations:
            # violations에 포함된 AI 개선 방안 추출
            for violation in analysis.violations:
                if isinstance(violation, dict) and 'ai_improvements' in violation:
                    ai_improvements.extend(violation['ai_improvements'])
        
        return JsonResponse({
            'success': True,
            'result': {
                'id': analysis.id,
                'overall_score': analysis.overall_score,
                'compliance_status': analysis.compliance_status,
                'risk_level': analysis.risk_level,
                'violations': analysis.violations,
                'recommendations': analysis.recommendations,
                'ai_improvements': ai_improvements,
                'input_type': analysis.input_type,
                'input_text': analysis.input_text,
                'created_at': analysis.created_at.isoformat()
            }
        })
        
    except ComplianceAnalysis.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '분석 결과를 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"분석 결과 조회 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'분석 결과 조회 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def upload_guideline(request):
    """의료 가이드라인 문서 업로드 API"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': '파일을 업로드해주세요.'
            })
        
        uploaded_file = request.FILES['file']
        title = request.POST.get('title', uploaded_file.name)
        category = request.POST.get('category', 'guidelines')
        description = request.POST.get('description', '')
        
        # 파일 타입 확인
        file_name = uploaded_file.name.lower()
        if file_name.endswith('.pdf'):
            doc_type = 'pdf'
        elif file_name.endswith(('.docx', '.doc')):
            doc_type = 'doc'
        elif file_name.endswith('.txt'):
            doc_type = 'txt'
        else:
            return JsonResponse({
                'success': False,
                'error': '지원하지 않는 파일 형식입니다.'
            })
        
        # 텍스트 추출 시도
        extracted_text = ""
        try:
            file_content = uploaded_file.read()
            if doc_type == 'pdf':
                extracted_text = TextExtractor.extract_from_pdf(file_content)
            elif doc_type == 'doc':
                extracted_text = TextExtractor.extract_from_docx(file_content)
            elif doc_type == 'txt':
                extracted_text = TextExtractor.extract_from_txt(file_content)
        except Exception as e:
            logger.warning(f"가이드라인 텍스트 추출 실패: {e}")
            # 텍스트 추출 실패해도 업로드는 허용
        
        # 파일 포인터를 처음으로 되돌림
        uploaded_file.seek(0)
        
        # DB에 저장
        guideline = MedicalGuideline.objects.create(
            title=title,
            category=category,
            description=description,
            document_type=doc_type,
            file=uploaded_file,
            extracted_text=extracted_text
        )
        
        return JsonResponse({
            'success': True,
            'guideline_id': guideline.id,
            'title': guideline.title,
            'extracted_text': extracted_text
        })
        
    except Exception as e:
        logger.error(f"가이드라인 업로드 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'가이드라인 업로드 중 오류가 발생했습니다: {str(e)}'
        })

@require_http_methods(["GET"])
def get_guideline(request, guideline_id):
    """가이드라인 상세 조회 API"""
    try:
        guideline = MedicalGuideline.objects.get(id=guideline_id)
        
        return JsonResponse({
            'success': True,
            'guideline': {
                'id': guideline.id,
                'title': guideline.title,
                'category': guideline.category,
                'category_display': guideline.get_category_display(),
                'description': guideline.description,
                'document_type': guideline.document_type,
                'file_name': guideline.file.name if guideline.file else '',
                'file_size_display': f"{guideline.file.size / 1024 / 1024:.2f} MB" if guideline.file else '0 MB',
                'uploaded_at': guideline.uploaded_at.isoformat(),
                'extracted_text': guideline.extracted_text[:1000] + '...' if len(guideline.extracted_text) > 1000 else guideline.extracted_text
            }
        })
        
    except MedicalGuideline.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '가이드라인을 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"가이드라인 조회 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'가이드라인 조회 중 오류가 발생했습니다: {str(e)}'
        })

@require_http_methods(["GET"])
def download_guideline(request, guideline_id):
    """가이드라인 다운로드 API"""
    try:
        guideline = MedicalGuideline.objects.get(id=guideline_id)
        
        if not guideline.file:
            return JsonResponse({
                'success': False,
                'error': '파일이 없습니다.'
            })
        
        response = HttpResponse(guideline.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{guideline.title}.{guideline.document_type}"'
        return response
        
    except MedicalGuideline.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '가이드라인을 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"가이드라인 다운로드 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'가이드라인 다운로드 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_guideline(request, guideline_id):
    """가이드라인 삭제 API"""
    try:
        guideline = MedicalGuideline.objects.get(id=guideline_id)
        guideline.delete()
        
        return JsonResponse({
            'success': True,
            'message': '가이드라인이 삭제되었습니다.'
        })
        
    except MedicalGuideline.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '가이드라인을 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"가이드라인 삭제 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'가이드라인 삭제 중 오류가 발생했습니다: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_analysis(request, analysis_id):
    """분석 결과 삭제 API"""
    try:
        analysis = ComplianceAnalysis.objects.get(id=analysis_id)
        analysis.delete()
        
        return JsonResponse({
            'success': True,
            'message': '분석 결과가 삭제되었습니다.'
        })
        
    except ComplianceAnalysis.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '분석 결과를 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"분석 결과 삭제 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'분석 결과 삭제 중 오류가 발생했습니다: {str(e)}'
        })

@require_http_methods(["GET"])
def export_pdf_report(request, analysis_id):
    """PDF 리포트 생성 및 다운로드"""
    try:
        analysis = ComplianceAnalysis.objects.get(id=analysis_id)
        
        # 간단한 HTML 리포트 생성 (실제로는 reportlab 등 사용)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>의료광고법 준수 검토 리포트</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .score {{ font-size: 24px; font-weight: bold; margin: 20px 0; }}
                .violation {{ background: #ffe6e6; padding: 10px; margin: 10px 0; border-left: 4px solid #ff0000; }}
                .recommendation {{ background: #e6ffe6; padding: 10px; margin: 10px 0; border-left: 4px solid #00ff00; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>의료광고법 준수 검토 리포트</h1>
                <p>분석일시: {analysis.created_at.strftime('%Y년 %m월 %d일 %H:%M')}</p>
            </div>
            
            <div class="score">
                준수 점수: {analysis.overall_score}/100
                <br>
                상태: {analysis.compliance_status}
                <br>
                위험도: {analysis.risk_level}
            </div>
            
            <h2>위반 항목 ({len(analysis.violations)}건)</h2>
            {''.join([f'<div class="violation"><strong>{v["type"]}</strong><br>{v["description"]}</div>' for v in analysis.violations])}
            
            <h2>개선 권장사항 ({len(analysis.recommendations)}건)</h2>
            {''.join([f'<div class="recommendation"><strong>원문:</strong> {r["original"]}<br><strong>개선안:</strong> {r["improved"]}</div>' for r in analysis.recommendations])}
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc;">
                <p><small>본 리포트는 2025년 의료법 및 의료광고법 기준으로 생성되었습니다.</small></p>
            </div>
        </body>
        </html>
        """
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="의료광고법-검토결과-{analysis_id}.pdf"'
        
        # 실제 PDF 생성은 reportlab 등을 사용해야 하지만, 여기서는 HTML을 반환
        response.write(html_content.encode('utf-8'))
        return response
        
    except ComplianceAnalysis.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '분석 결과를 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"PDF 리포트 생성 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'PDF 리포트 생성 중 오류가 발생했습니다: {str(e)}'
        })

@require_http_methods(["GET"])
def get_statistics(request):
    """통계 데이터 API"""
    try:
        # 최근 30일 통계
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # 일별 분석 수
        daily_stats = ComplianceAnalysis.objects.filter(
            created_at__gte=thirty_days_ago
        ).extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        # 위험도별 통계
        risk_stats = ComplianceAnalysis.objects.values('risk_level').annotate(count=Count('id'))
        
        # 준수 상태별 통계
        status_stats = ComplianceAnalysis.objects.values('compliance_status').annotate(count=Count('id'))
        
        return JsonResponse({
            'success': True,
            'daily_stats': list(daily_stats),
            'risk_stats': list(risk_stats),
            'status_stats': list(status_stats),
        })
        
    except Exception as e:
        logger.error(f"통계 데이터 조회 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'통계 데이터 조회 중 오류가 발생했습니다: {str(e)}'
        })

def get_detailed_report(request, analysis_id):
    """상세 리포트 API"""
    try:
        analysis = get_object_or_404(ComplianceAnalysis, id=analysis_id)
        
        # 상세 위반 정보가 없는 경우 기본값 설정
        if not hasattr(analysis, 'detailed_violations') or not analysis.detailed_violations:
            analysis.detailed_violations = []
        
        if not hasattr(analysis, 'compliance_checklist') or not analysis.compliance_checklist:
            analysis.compliance_checklist = []
        
        if not hasattr(analysis, 'review_guidance') or not analysis.review_guidance:
            analysis.review_guidance = {}
        
        # 위반 항목별 우선순위 및 상세 정보 생성
        violation_details = []
        for violation in analysis.detailed_violations:
            # 위험도에 따른 우선순위 결정
            if violation['severity'] == 'high':
                priority = '긴급'
                estimated_fine = '1,000만원 이하'
                compliance_difficulty = '높음'
                estimated_time = '1-2주'
                risk_score = 90
            elif violation['severity'] == 'medium':
                priority = '높음'
                estimated_fine = '500만원 이하'
                compliance_difficulty = '보통'
                estimated_time = '3-5일'
                risk_score = 60
            else:
                priority = '보통'
                estimated_fine = '100만원 이하'
                compliance_difficulty = '낮음'
                estimated_time = '1-2일'
                risk_score = 30
            
            violation_details.append({
                'category': violation['category'],
                'title': violation['title'],
                'keyword': violation['keyword'],
                'context': violation['context'],
                'severity': violation['severity'],
                'priority': priority,
                'estimated_fine': estimated_fine,
                'compliance_difficulty': compliance_difficulty,
                'estimated_time': estimated_time,
                'risk_score': risk_score,
                'penalty': violation['penalty'],
                'legal_basis': violation['legal_basis'],
                'improvement_guide': violation['improvement_guide']
            })
        
        # 전체 위험도 계산
        total_risk_score = sum(v['risk_score'] for v in violation_details) if violation_details else 0
        overall_risk_level = '높음' if total_risk_score > 100 else '보통' if total_risk_score > 50 else '낮음'
        
        # 준수 타임라인 생성
        compliance_timeline = []
        if violation_details:
            high_priority = [v for v in violation_details if v['priority'] == '긴급']
            medium_priority = [v for v in violation_details if v['priority'] == '높음']
            low_priority = [v for v in violation_details if v['priority'] == '보통']
            
            if high_priority:
                compliance_timeline.append({
                    'period': '즉시 (24시간 이내)',
                    'actions': [f"{v['category']}: {v['keyword']} 수정" for v in high_priority],
                    'priority': '긴급'
                })
            
            if medium_priority:
                compliance_timeline.append({
                    'period': '1주일 이내',
                    'actions': [f"{v['category']}: {v['keyword']} 수정" for v in medium_priority],
                    'priority': '높음'
                })
            
            if low_priority:
                compliance_timeline.append({
                    'period': '2주일 이내',
                    'actions': [f"{v['category']}: {v['keyword']} 수정" for v in low_priority],
                    'priority': '보통'
                })
        
        # 비용 분석
        total_estimated_fine = sum(
            int(v['estimated_fine'].replace('만원 이하', '').replace(',', '')) * 10000 
            for v in violation_details
        ) if violation_details else 0
        
        # 법적 영향 분석
        legal_impact = {
            'criminal_liability': '있음' if any(v['severity'] == 'high' for v in violation_details) else '없음',
            'administrative_penalty': '있음' if violation_details else '없음',
            'business_suspension': '있음' if any(v['severity'] == 'high' for v in violation_details) else '없음',
            'reputation_damage': '높음' if total_risk_score > 100 else '보통' if total_risk_score > 50 else '낮음'
        }
        
        # 권장 행동 항목
        recommended_actions = []
        if violation_details:
            for violation in violation_details:
                recommended_actions.append({
                    'action': f"{violation['keyword']} 표현 수정",
                    'category': violation['category'],
                    'priority': violation['priority'],
                    'timeline': violation['estimated_time'],
                    'description': violation['improvement_guide']
                })
        
        detailed_report = {
            'analysis_id': analysis.id,
            'analysis_date': analysis.created_at.strftime('%Y-%m-%d %H:%M'),
            'input_type': analysis.input_type,
            'overall_score': analysis.overall_score,
            'compliance_status': analysis.compliance_status,
            'risk_level': analysis.risk_level,
            'violation_details': violation_details,
            'total_risk_score': total_risk_score,
            'overall_risk_level': overall_risk_level,
            'compliance_timeline': compliance_timeline,
            'total_estimated_fine': total_estimated_fine,
            'legal_impact': legal_impact,
            'recommended_actions': recommended_actions,
            'compliance_checklist': analysis.compliance_checklist,
            'review_guidance': analysis.review_guidance
        }
        
        return JsonResponse(detailed_report)
        
    except Exception as e:
        print(f"상세 리포트 생성 오류: {str(e)}")
        return JsonResponse({
            'error': f'상세 리포트 생성 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

def _estimate_fine(violation):
    """위반 항목별 예상 벌금 추정"""
    penalty_text = violation.get('penalty', '')
    
    if '1,000만원' in penalty_text:
        return '최대 1,000만원'
    elif '3,000만원' in penalty_text:
        return '최대 3,000만원'
    elif '과태료' in penalty_text:
        if '300만원' in penalty_text:
            return '최대 300만원'
        elif '100만원' in penalty_text:
            return '최대 100만원'
        else:
            return '과태료'
    else:
        return '처벌 수준 확인 필요'

def _assess_compliance_difficulty(violation):
    """준수 난이도 평가"""
    category = violation.get('category', '')
    
    if '과장·절대적 표현' in category:
        return '보통 - 표현 수정 필요'
    elif '환자체험담·후기' in category:
        return '쉬움 - 내용 삭제'
    elif 'SNS 미심의' in category:
        return '보통 - 사전심의 절차'
    elif '환자 유인·알선' in category:
        return '쉬움 - 표현 삭제'
    else:
        return '보통'

def _estimate_time_to_fix(violation):
    """수정 소요 시간 추정"""
    category = violation.get('category', '')
    
    if '과장·절대적 표현' in category:
        return '1-2일'
    elif '환자체험담·후기' in category:
        return '즉시'
    elif 'SNS 미심의' in category:
        return '1-2주 (심의 기간)'
    elif '환자 유인·알선' in category:
        return '즉시'
    else:
        return '1-3일'

def _analyze_overall_risk(analysis):
    """전체 위험도 분석"""
    high_count = sum(1 for v in analysis.violations if v.get('severity') == 'high')
    medium_count = sum(1 for v in analysis.violations if v.get('severity') == 'medium')
    low_count = sum(1 for v in analysis.violations if v.get('severity') == 'low')
    
    total_violations = len(analysis.violations)
    
    if high_count >= 3:
        risk_level = '매우 높음'
        risk_description = '즉시 수정이 필요한 심각한 위반 사항이 다수 발견되었습니다.'
    elif high_count >= 1:
        risk_level = '높음'
        risk_description = '고위험 위반 사항이 발견되어 신속한 수정이 필요합니다.'
    elif medium_count >= 2:
        risk_level = '보통'
        risk_description = '중간 수준의 위반 사항들이 발견되었습니다.'
    elif total_violations > 0:
        risk_level = '낮음'
        risk_description = '경미한 위반 사항들이 발견되었습니다.'
    else:
        risk_level = '없음'
        risk_description = '위반 사항이 발견되지 않았습니다.'
    
    return {
        'level': risk_level,
        'description': risk_description,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
        'total_count': total_violations
    }

def _generate_compliance_timeline(detailed_violations):
    """준수 타임라인 생성"""
    timeline = []
    
    # 즉시 수정 가능한 항목들
    immediate_fixes = [v for v in detailed_violations if '즉시' in v.get('time_to_fix', '')]
    if immediate_fixes:
        timeline.append({
            'phase': '즉시 수정',
            'description': '즉시 수정 가능한 위반 사항들',
            'items': [v['category'] for v in immediate_fixes],
            'estimated_time': '즉시',
            'priority': 1
        })
    
    # 단기 수정 항목들
    short_term_fixes = [v for v in detailed_violations if '1-3일' in v.get('time_to_fix', '')]
    if short_term_fixes:
        timeline.append({
            'phase': '단기 수정',
            'description': '1-3일 내 수정 가능한 항목들',
            'items': [v['category'] for v in short_term_fixes],
            'estimated_time': '1-3일',
            'priority': 2
        })
    
    # 중기 수정 항목들
    medium_term_fixes = [v for v in detailed_violations if '1-2주' in v.get('time_to_fix', '')]
    if medium_term_fixes:
        timeline.append({
            'phase': '중기 수정',
            'description': '심의 절차가 필요한 항목들',
            'items': [v['category'] for v in medium_term_fixes],
            'estimated_time': '1-2주',
            'priority': 3
        })
    
    return timeline

def _calculate_cost_analysis(analysis):
    """비용 분석"""
    total_estimated_fine = 0
    review_fees = 0
    
    # 벌금 추정
    for violation in analysis.violations:
        penalty = violation.get('penalty', '')
        if '1,000만원' in penalty:
            total_estimated_fine += 10000000
        elif '3,000만원' in penalty:
            total_estimated_fine += 30000000
    
    # 심의 수수료
    compliance_checklist = getattr(analysis, 'compliance_checklist', {}) or {}
    if compliance_checklist.get('pre_review_required'):
        fee_text = compliance_checklist.get('estimated_review_fee', '11만원')
        if '11만원' in fee_text:
            review_fees = 110000
        elif '22만원' in fee_text:
            review_fees = 220000
        elif '33만원' in fee_text:
            review_fees = 330000
        elif '44만원' in fee_text:
            review_fees = 440000
        elif '55만원' in fee_text:
            review_fees = 550000
    
    return {
        'total_estimated_fine': total_estimated_fine,
        'review_fees': review_fees,
        'total_cost': total_estimated_fine + review_fees,
        'cost_breakdown': {
            'penalties': total_estimated_fine,
            'review_fees': review_fees
        }
    }

def _analyze_legal_implications(analysis):
    """법적 영향 분석"""
    implications = []
    
    for violation in analysis.violations:
        severity = violation.get('severity', '')
        penalty = violation.get('penalty', '')
        
        if severity == 'high':
            if '징역' in penalty:
                implications.append({
                    'type': '형사처벌',
                    'description': f"{violation['category']}: {penalty}",
                    'severity': '심각'
                })
            elif '업무정지' in penalty:
                implications.append({
                    'type': '행정처분',
                    'description': f"{violation['category']}: {penalty}",
                    'severity': '심각'
                })
        elif severity == 'medium':
            implications.append({
                'type': '행정처분',
                'description': f"{violation['category']}: {penalty}",
                'severity': '보통'
            })
    
    return implications

def _parse_fine_amount(fine_text):
    """벌금 텍스트를 숫자로 파싱"""
    try:
        if '1,000만원' in fine_text:
            return 10000000
        elif '3,000만원' in fine_text:
            return 30000000
        elif '300만원' in fine_text:
            return 3000000
        elif '100만원' in fine_text:
            return 1000000
        else:
            return 0
    except:
        return 0

def _generate_recommended_actions(detailed_violations):
    """권장 행동 항목 생성"""
    actions = []
    
    # 고위험 항목 우선 처리
    high_priority = [v for v in detailed_violations if v.get('severity') == 'high']
    if high_priority:
        actions.append({
            'priority': 1,
            'action': '고위험 위반 사항 즉시 수정',
            'description': '형사처벌 가능성이 있는 위반 사항들을 우선적으로 수정하세요.',
            'items': [v['category'] for v in high_priority],
            'deadline': '즉시',
            'estimated_cost': sum(_parse_fine_amount(v.get('estimated_fine', '0')) for v in high_priority)
        })
    
    # SNS 관련 항목
    sns_violations = [v for v in detailed_violations if 'SNS' in v.get('category', '')]
    if sns_violations:
        actions.append({
            'priority': 2,
            'action': '대한의사협회 사전심의 접수',
            'description': 'SNS 플랫폼 광고 시 사전심의가 필수입니다.',
            'contact': '대한의사협회 의료광고심의위원회 (02-794-2474)',
            'deadline': '광고 게시 전',
            'estimated_cost': 110000  # 기본 심의료
        })
    
    # 중위험 항목
    medium_priority = [v for v in detailed_violations if v.get('severity') == 'medium']
    if medium_priority:
        actions.append({
            'priority': 3,
            'action': '중위험 위반 사항 수정',
            'description': '행정처분 가능성이 있는 위반 사항들을 수정하세요.',
            'items': [v['category'] for v in medium_priority],
            'deadline': '1주일 내',
            'estimated_cost': 0
        })
    
    return actions

def guideline_management(request):
    """가이드라인 관리 메인 페이지"""
    categories = GuidelineDocument.objects.values_list('category', flat=True).distinct()
    documents = GuidelineDocument.objects.filter(is_active=True).order_by('category', 'order', '-created_at')
    
    # 카테고리별 문서 수
    category_counts = {}
    for category in categories:
        category_counts[category] = documents.filter(category=category).count()
    
    # 최근 업데이트
    recent_updates = GuidelineUpdate.objects.select_related('document').order_by('-created_at')[:10]
    
    # AI 분석 통계
    ai_analysis_count = AIAnalysisResult.objects.count()

    # 활성 문서 수
    active_documents_count = documents.count()
    
    context = {
        'documents': documents,
        'category_counts': category_counts,
        'recent_updates': recent_updates,
        'ai_analysis_count': ai_analysis_count,
        'categories': GuidelineDocument._meta.get_field('category').choices,
        'active_documents_count': active_documents_count,
    }
    
    return render(request, 'compliance_checker/guideline_management.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def create_guideline_document(request):
    """새 가이드라인 문서 생성"""
    try:
        data = json.loads(request.body)
        
        document = GuidelineDocument.objects.create(
            title=data.get('title'),
            category=data.get('category'),
            description=data.get('description', ''),
            content=data.get('content'),
            source=data.get('source', ''),
            effective_date=data.get('effective_date'),
            order=data.get('order', 0)
        )
        
        # 업데이트 이력 생성
        GuidelineUpdate.objects.create(
            document=document,
            update_type='new_document',
            new_content=data.get('content'),
            update_reason='새 문서 생성',
            updated_by=data.get('updated_by', '시스템')
        )
        
        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'message': '가이드라인 문서가 성공적으로 생성되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'문서 생성 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_guideline_document(request, document_id):
    """가이드라인 문서 업데이트"""
    try:
        document = get_object_or_404(GuidelineDocument, id=document_id)
        data = json.loads(request.body)
        
        # 이전 내용 저장
        previous_content = document.content
        
        # 문서 업데이트
        document.title = data.get('title', document.title)
        document.category = data.get('category', document.category)
        document.description = data.get('description', document.description)
        document.content = data.get('content', document.content)
        document.source = data.get('source', document.source)
        document.effective_date = data.get('effective_date', document.effective_date)
        document.order = data.get('order', document.order)
        document.save()
        
        # 업데이트 이력 생성
        GuidelineUpdate.objects.create(
            document=document,
            update_type='content_update',
            previous_content=previous_content,
            new_content=data.get('content'),
            update_reason=data.get('update_reason', '내용 업데이트'),
            updated_by=data.get('updated_by', '시스템')
        )
        
        return JsonResponse({
            'success': True,
            'message': '가이드라인 문서가 성공적으로 업데이트되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'문서 업데이트 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def get_guideline_document(request, document_id):
    """가이드라인 문서 조회"""
    try:
        document = get_object_or_404(GuidelineDocument, id=document_id)
        
        # 업데이트 이력 조회
        updates = document.updates.order_by('-created_at')[:10]
        
        # AI 분석 결과 조회
        ai_analyses = document.ai_analyses.order_by('-created_at')[:5]
        
        return JsonResponse({
            'success': True,
            'document': {
                'id': document.id,
                'title': document.title,
                'category': document.category,
                'category_display': document.category_display,
                'description': document.description,
                'content': document.content,
                'source': document.source,
                'effective_date': document.effective_date.isoformat() if document.effective_date else None,
                'order': document.order,
                'created_at': document.created_at.isoformat(),
                'updated_at': document.updated_at.isoformat(),
            },
            'updates': list(updates.values('update_type', 'update_reason', 'updated_by', 'created_at')),
            'ai_analyses': list(ai_analyses.values('analysis_type', 'ai_model_used', 'processing_time', 'created_at'))
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'문서 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def analyze_with_ai(request, document_id):
    """AI를 이용한 가이드라인 분석"""
    try:
        document = get_object_or_404(GuidelineDocument, id=document_id)
        data = json.loads(request.body)
        analysis_type = data.get('analysis_type', 'content_analysis')
        
        # OpenAI API 키 설정 (실제 환경에서는 환경변수로 관리)
        # openai.api_key = "your-api-key"
        
        # 분석 프롬프트 생성
        prompts = {
            'content_analysis': f"""
            다음 의료법/광고법 가이드라인 문서를 분석해주세요:
            
            제목: {document.title}
            카테고리: {document.category_display}
            내용: {document.content}
            
            다음 항목들을 분석해주세요:
            1. 주요 내용 요약
            2. 핵심 포인트
            3. 의료진이 주의해야 할 사항
            4. 광고 시 준수해야 할 규칙
            5. 위반 시 예상되는 처벌
            """,
            'compliance_check': f"""
            다음 가이드라인 문서의 준수성을 검토해주세요:
            
            제목: {document.title}
            내용: {document.content}
            
            다음 항목들을 검토해주세요:
            1. 현재 의료광고법과의 일치성
            2. 잠재적 위반 요소
            3. 준수 난이도 평가
            4. 개선이 필요한 부분
            5. 권장사항
            """,
            'risk_assessment': f"""
            다음 가이드라인 문서의 위험도를 평가해주세요:
            
            제목: {document.title}
            내용: {document.content}
            
            다음 항목들을 평가해주세요:
            1. 전체 위험도 (낮음/보통/높음)
            2. 주요 위험 요소
            3. 위험 발생 가능성
            4. 위험 발생 시 영향도
            5. 위험 완화 방안
            """,
            'improvement_suggestions': f"""
            다음 가이드라인 문서의 개선 방안을 제안해주세요:
            
            제목: {document.title}
            내용: {document.content}
            
            다음 항목들을 제안해주세요:
            1. 내용 개선 방안
            2. 구조 개선 방안
            3. 가독성 향상 방안
            4. 실용성 개선 방안
            5. 최신 법령 반영 방안
            """
        }
        
        # AI 분석 실행 (실제 OpenAI API 호출 대신 시뮬레이션)
        analysis_result = {
            'analysis_type': analysis_type,
            'summary': f'{document.title}에 대한 {analysis_type} 분석 결과입니다.',
            'key_points': ['주요 포인트 1', '주요 포인트 2', '주요 포인트 3'],
            'recommendations': ['권장사항 1', '권장사항 2', '권장사항 3'],
            'risk_level': 'medium',
            'compliance_score': 85
        }
        
        # AI 분석 결과 저장
        ai_result = AIAnalysisResult.objects.create(
            document=document,
            analysis_type=analysis_type,
            analysis_result=analysis_result,
            ai_model_used='GPT-4 (시뮬레이션)',
            processing_time=2.5
        )
        
        return JsonResponse({
            'success': True,
            'analysis_id': ai_result.id,
            'result': analysis_result
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'AI 분석 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_guideline_document(request, document_id):
    """가이드라인 문서 삭제"""
    try:
        document = get_object_or_404(GuidelineDocument, id=document_id)
        document.delete()
        
        return JsonResponse({
            'success': True,
            'message': '가이드라인 문서가 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'문서 삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

def guideline_updates(request):
    """가이드라인 업데이트 이력 페이지"""
    updates = GuidelineUpdate.objects.select_related('document').order_by('-created_at')
    
    # 필터링
    update_type = request.GET.get('type', '')
    if update_type:
        updates = updates.filter(update_type=update_type)
    
    # 페이지네이션
    paginator = Paginator(updates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'updates': page_obj,
        'update_types': GuidelineUpdate._meta.get_field('update_type').choices,
    }
    
    return render(request, 'compliance_checker/guideline_updates.html', context)

def ai_analysis_history(request):
    """AI 분석 이력 페이지"""
    analyses = AIAnalysisResult.objects.select_related('document').order_by('-created_at')
    
    # 필터링
    analysis_type = request.GET.get('type', '')
    if analysis_type:
        analyses = analyses.filter(analysis_type=analysis_type)
    
    # 페이지네이션
    paginator = Paginator(analyses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'analyses': page_obj,
        'analysis_types': AIAnalysisResult._meta.get_field('analysis_type').choices,
    }
    
    return render(request, 'compliance_checker/ai_analysis_history.html', context)

@require_http_methods(["GET"])
def get_ai_analysis_result(request, analysis_id):
    """AI 분석 결과 조회 API"""
    try:
        analysis = AIAnalysisResult.objects.get(id=analysis_id)
        
        return JsonResponse({
            'success': True,
            'result': {
                'id': analysis.id,
                'analysis_type': analysis.analysis_type,
                'get_analysis_type_display': analysis.get_analysis_type_display(),
                'ai_model_used': analysis.ai_model_used,
                'processing_time': analysis.processing_time,
                'created_at': analysis.created_at.isoformat(),
                'analysis_result': analysis.analysis_result,
                'result': analysis.result,
                'document': {
                    'id': analysis.document.id,
                    'title': analysis.document.title,
                    'category_display': analysis.document.get_category_display()
                }
            }
        })
        
    except AIAnalysisResult.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'AI 분석 결과를 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"AI 분석 결과 조회 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'AI 분석 결과 조회 중 오류가 발생했습니다: {str(e)}'
        })

@require_http_methods(["GET"])
def get_guideline_update_detail(request, update_id):
    """가이드라인 업데이트 상세 조회 API"""
    try:
        update = GuidelineUpdate.objects.get(id=update_id)
        
        return JsonResponse({
            'success': True,
            'update': {
                'id': update.id,
                'update_type': update.update_type,
                'get_update_type_display': update.get_update_type_display(),
                'updated_by': update.updated_by,
                'created_at': update.created_at.isoformat(),
                'update_reason': update.update_reason,
                'changes': update.changes,
                'document': {
                    'id': update.document.id,
                    'title': update.document.title,
                    'category_display': update.document.get_category_display()
                }
            }
        })
        
    except GuidelineUpdate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '업데이트 정보를 찾을 수 없습니다.'
        })
    except Exception as e:
        logger.error(f"업데이트 정보 조회 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'업데이트 정보 조회 중 오류가 발생했습니다: {str(e)}'
        })

def get_ai_improvement_suggestions(violation_data, original_text):
    """Claude API를 사용하여 위반 항목에 대한 개선 방안 생성"""
    if not anthropic:
        return {
            'success': False,
            'error': 'Claude API가 설정되지 않았습니다.',
            'suggestions': []
        }
    
    try:
        # 위반 정보 구성
        violation_info = {
            'category': violation_data.get('category', ''),
            'keyword': violation_data.get('keyword', ''),
            'context': violation_data.get('context', ''),
            'legal_basis': violation_data.get('legal_basis', ''),
            'penalty': violation_data.get('penalty', '')
        }
        
        # Claude API 요청 프롬프트 구성
        prompt = f"""
당신은 의료광고법 준수 전문가입니다. 다음 위반 항목에 대해 구체적이고 실용적인 개선 방안을 제시해주세요.

**위반 정보:**
- 위반 유형: {violation_info['category']}
- 발견된 키워드: {violation_info['keyword']}
- 위반 문맥: "{violation_info['context']}"
- 법적 근거: {violation_info['legal_basis']}
- 처벌 내용: {violation_info['penalty']}

**원본 텍스트 (관련 부분):**
{original_text[:1000]}...

**요청사항:**
1. 위반 키워드를 적절한 대체 표현으로 변경하는 구체적인 제안
2. 문맥을 고려한 전체 문장 개선 방안
3. 의료광고법을 준수하면서도 효과적인 표현 방법
4. 추가 주의사항이나 권장사항

다음 JSON 형식으로 응답해주세요:
{{
    "improved_keyword": "대체 키워드",
    "improved_sentence": "개선된 문장",
    "alternative_expressions": ["대안 표현 1", "대안 표현 2"],
    "additional_recommendations": ["추가 권장사항 1", "추가 권장사항 2"],
    "legal_compliance_notes": "법적 준수 관련 참고사항"
}}
"""
        
        # Claude API 호출
        response = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # 응답 파싱
        content = response.content[0].text
        
        # JSON 추출 시도
        try:
            # JSON 부분만 추출
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = content[json_start:json_end]
                suggestions = json.loads(json_str)
            else:
                # JSON이 없으면 텍스트를 파싱
                suggestions = {
                    'improved_keyword': '대체 표현',
                    'improved_sentence': content,
                    'alternative_expressions': [],
                    'additional_recommendations': [],
                    'legal_compliance_notes': 'AI가 제안한 개선 방안입니다.'
                }
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트 그대로 사용
            suggestions = {
                'improved_keyword': '대체 표현',
                'improved_sentence': content,
                'alternative_expressions': [],
                'additional_recommendations': [],
                'legal_compliance_notes': 'AI가 제안한 개선 방안입니다.'
            }
        
        return {
            'success': True,
            'suggestions': suggestions,
            'raw_response': content
        }
        
    except Exception as e:
        logger.error(f"Claude API 호출 오류: {e}")
        return {
            'success': False,
            'error': f'AI 개선 방안 생성 중 오류가 발생했습니다: {str(e)}',
            'suggestions': []
        }

@csrf_exempt
@require_http_methods(["POST"])
def get_violation_improvements(request):
    """위반 항목에 대한 AI 개선 방안 조회 API"""
    try:
        data = json.loads(request.body)
        violation_data = data.get('violation', {})
        original_text = data.get('original_text', '')
        
        if not violation_data or not original_text:
            return JsonResponse({
                'success': False,
                'error': '위반 정보와 원본 텍스트가 필요합니다.'
            }, status=400)
        
        # AI 개선 방안 생성
        result = get_ai_improvement_suggestions(violation_data, original_text)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"위반 개선 방안 조회 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'개선 방안 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def rewrite_text_with_ai(request):
    """AI를 이용한 텍스트 재작성 API"""
    try:
        data = json.loads(request.body)
        original_text = data.get('original_text', '')
        violations = data.get('violations', [])
        
        if not original_text:
            return JsonResponse({
                'success': False,
                'error': '원본 텍스트가 필요합니다.'
            }, status=400)
        
        if not anthropic:
            return JsonResponse({
                'success': False,
                'error': 'Claude API가 설정되지 않았습니다.'
            }, status=400)
        
        # AI 텍스트 재작성 실행
        result = rewrite_text_using_ai(original_text, violations)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"텍스트 재작성 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': f'텍스트 재작성 중 오류가 발생했습니다: {str(e)}'
        }, status=500)

def rewrite_text_using_ai(original_text: str, violations: List[Dict]) -> Dict:
    """AI를 사용하여 위반 사항을 수정한 새로운 텍스트 생성"""
    try:
        # 위반 사항 요약
        violation_summary = []
        for violation in violations:
            violation_summary.append({
                'category': violation.get('category', ''),
                'keyword': violation.get('keyword', ''),
                'context': violation.get('context', ''),
                'legal_basis': violation.get('legal_basis', ''),
                'penalty': violation.get('penalty', '')
            })
        
        # Claude API 요청 프롬프트 구성
        prompt = f"""
당신은 의료광고법 준수 전문가입니다. 다음 원본 텍스트에서 발견된 위반 사항들을 수정하여 의료광고법을 준수하는 새로운 텍스트를 작성해주세요.

**원본 텍스트:**
{original_text}

**발견된 위반 사항들:**
"""
        
        for i, violation in enumerate(violation_summary, 1):
            prompt += f"""
{i}. 위반 유형: {violation['category']}
   - 발견된 키워드: {violation['keyword']}
   - 위반 문맥: "{violation['context']}"
   - 법적 근거: {violation['legal_basis']}
   - 처벌 내용: {violation['penalty']}
"""
        
        prompt += """
**요청사항:**
1. 원본 텍스트의 전체 구조와 길이를 그대로 유지하면서 위반 사항들만 수정해주세요
2. 원본 텍스트의 의미와 의도를 최대한 유지하면서 의료광고법을 준수하도록 수정해주세요
3. 위반된 부분만 개선된 표현으로 교체하고, 나머지 부분은 그대로 유지해주세요
4. 객관적이고 사실에 근거한 표현으로 변경해주세요
5. 과장된 표현이나 절대적 표현을 제거하고 적절한 대체 표현을 사용해주세요
6. 환자 후기나 경험담 관련 내용이 있다면 제거하거나 객관적 정보로 변경해주세요
7. 원본 텍스트의 전체적인 분량과 구조를 유지해주세요

**응답 형식:**
다음 JSON 형식으로 응답해주세요:
{
    "rewritten_text": "수정된 전체 텍스트",
    "changes_made": [
        {
            "original": "원본 표현",
            "improved": "개선된 표현",
            "reason": "수정 이유"
        }
    ],
    "compliance_notes": "준수 관련 참고사항",
    "word_count": "수정된 텍스트의 단어 수",
    "estimated_compliance_score": "예상 준수도 점수 (0-100)"
}
"""
        
        # Claude API 호출
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # 응답 파싱
        content = response.content[0].text
        
        # JSON 추출 시도
        try:
            # JSON 부분만 추출
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
            else:
                # JSON이 없으면 기본 구조로 생성
                result = {
                    'rewritten_text': content,
                    'changes_made': [],
                    'compliance_notes': 'AI가 제안한 수정된 텍스트입니다.',
                    'word_count': len(content.split()),
                    'estimated_compliance_score': 85
                }
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 구조로 생성
            result = {
                'rewritten_text': content,
                'changes_made': [],
                'compliance_notes': 'AI가 제안한 수정된 텍스트입니다.',
                'word_count': len(content.split()),
                'estimated_compliance_score': 85
            }
        
        # 수정된 부분만 추출 (수정 사항만 복사용)
        modified_parts_only = extract_modified_parts_only(result.get('changes_made', []))
        
        # 원본에 수정사항을 적용한 전체 텍스트 생성 (재작성된 전체 텍스트 복사용)
        rewritten_full_text = apply_changes_to_original(original_text, result.get('changes_made', []))
        
        # 결과에 추가
        result['modified_text_only'] = modified_parts_only
        result['rewritten_full_text'] = rewritten_full_text
        
        return {
            'success': True,
            'result': result,
            'raw_response': content
        }
        
    except Exception as e:
        logger.error(f"AI 텍스트 재작성 오류: {e}")
        return {
            'success': False,
            'error': f'AI 텍스트 재작성 중 오류가 발생했습니다: {str(e)}',
            'result': None
        }

def extract_modified_parts_only(changes_made: List[Dict]) -> str:
    """수정된 부분만 추출 (수정 사항만 복사용)"""
    try:
        if not changes_made:
            return "수정된 내용이 없습니다."
        
        # 수정된 부분만 추출하여 정리
        modified_parts = []
        for change in changes_made:
            original = change.get('original', '').strip()
            improved = change.get('improved', '').strip()
            reason = change.get('reason', '').strip()
            
            if original and improved:
                modified_parts.append(f"원본: {original}\n개선: {improved}\n이유: {reason}\n")
        
        if modified_parts:
            return "\n".join(modified_parts)
        else:
            return "수정된 내용이 없습니다."
        
    except Exception as e:
        logger.error(f"수정된 부분 추출 오류: {e}")
        return "수정된 내용을 추출할 수 없습니다."

def apply_changes_to_original(original_text: str, changes_made: List[Dict]) -> str:
    """원본 텍스트에 수정사항을 적용한 전체 텍스트 생성 (재작성된 전체 텍스트 복사용)"""
    try:
        if not changes_made:
            return original_text
        
        # 수정된 텍스트 생성
        modified_text = original_text
        
        # 변경사항을 역순으로 적용 (뒤에서부터 수정하여 인덱스 변화 방지)
        for change in reversed(changes_made):
            original = change.get('original', '')
            improved = change.get('improved', '')
            
            if original and improved:
                # 원본 텍스트에서 해당 부분을 개선된 표현으로 교체
                modified_text = modified_text.replace(original, improved)
        
        return modified_text
        
    except Exception as e:
        logger.error(f"수정사항 적용 오류: {e}")
        return original_text
