import re
import json
import os
from typing import Dict, List, Tuple, Any
from .models import ComplianceRule, ComplianceKeyword, RecommendedExpression

# Claude API 설정
try:
    from anthropic import Anthropic
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    anthropic = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
except ImportError:
    anthropic = None

class ComplianceAnalyzer:
    """의료광고법 준수 검토 분석기"""
    
    def __init__(self):
        self.rules = self._load_rules_from_db()
        print(f"[DEBUG] 로드된 규칙 수: {len(self.rules)}")
        try:
            self.keywords = self._load_keywords_from_db()
            print(f"[DEBUG] 로드된 키워드 카테고리: {list(self.keywords.keys())}")
            for category, keywords in self.keywords.items():
                print(f"[DEBUG] {category}: {len(keywords)}개 키워드")
        except Exception as e:
            print(f"[DEBUG] 키워드 로드 실패: {e}")
            self.keywords = {}
        try:
            self.recommended_expressions = self._load_recommended_expressions_from_db()
        except:
            self.recommended_expressions = []
    
    def _load_rules_from_db(self) -> List[ComplianceRule]:
        """데이터베이스에서 규칙 로드"""
        return list(ComplianceRule.objects.filter(is_active=True))
    
    def _load_keywords_from_db(self) -> Dict[str, List[str]]:
        """데이터베이스에서 키워드 로드"""
        keywords_dict = {}
        try:
            for rule in self.rules:
                try:
                    keywords = list(ComplianceKeyword.objects.filter(
                        rule=rule, 
                        is_active=True
                    ).values_list('keyword', flat=True))
                    keywords_dict[rule.category] = keywords
                except:
                    keywords_dict[rule.category] = []
        except:
            # 기본 키워드 제공 (PDF 텍스트에서 발견될 수 있는 키워드들 포함)
            keywords_dict = {
                '과장·절대적 표현': ['최고', '최고의', '완벽', '완전', '절대', '보장', '무통증', '완벽하게', '전혀', '100%'],
                '비교광고': ['비교', '더 나은', '우수한', '다른 곳은', '다른 병원'],
                '환자 후기·경험담': ['후기', '경험담', '환자분', '님의', '솔직한 후기', '생생 후기', '실제로'],
                'SNS 미심의 광고': ['인스타그램', '페이스북', '유튜브']
            }
        return keywords_dict
    
    def _load_recommended_expressions_from_db(self) -> List[Dict]:
        """데이터베이스에서 권장 표현 로드"""
        try:
            return list(RecommendedExpression.objects.filter(
                is_active=True
            ).values())
        except:
            return []
    
    def analyze_text(self, text: str, source_type: str = "text") -> Dict[str, Any]:
        """텍스트 분석 및 준수 검토"""
        try:
            # 디버깅을 위한 로깅
            print(f"[DEBUG] 분석할 텍스트 길이: {len(text) if text else 0}")
            print(f"[DEBUG] 텍스트 미리보기: {text[:100] if text else 'None'}...")
            
            if not text or not text.strip():
                print("[DEBUG] 빈 텍스트로 인한 오류 반환")
                return {
                    'overall_score': 0,
                    'compliance_status': '분석 불가',
                    'risk_level': 'high',
                    'violations': ['텍스트를 추출할 수 없습니다.'],
                    'recommendations': ['유효한 URL을 입력하거나 텍스트를 직접 입력해주세요.'],
                    'detailed_violations': [],
                    'compliance_checklist': [],
                    'review_guidance': {},
                    'extracted_text': text or '',
                    'text_analysis': {
                        'total_characters': 0,
                        'total_words': 0,
                        'total_sentences': 0,
                        'text_quality': 'empty'
                    },
                    'legal_analysis': {
                        'applicable_laws': [],
                        'legal_risks': [],
                        'compliance_requirements': []
                    }
                }
            
            # 텍스트 분석
            text_analysis = self._analyze_text_quality(text)
            
            violations = []
            detailed_violations = []
            recommendations = []
            total_score = 100
            
            # 각 규칙별 분석
            for rule in self.rules:
                try:
                    rule_keywords = self.keywords.get(rule.category, [])
                    print(f"[DEBUG] 규칙 '{rule.category}' 분석 중, 키워드 수: {len(rule_keywords)}")
                    if rule_keywords:
                        print(f"[DEBUG] 키워드 예시: {rule_keywords[:5]}")
                    
                    found_violations = self._check_rule_violations(text, rule, rule_keywords)
                    print(f"[DEBUG] 발견된 위반 수: {len(found_violations) if found_violations else 0}")
                    
                    if found_violations:
                        violations.append({
                            'category': rule.category,
                            'title': rule.title,
                            'severity': rule.severity,
                            'count': len(found_violations),
                            'legal_basis': rule.legal_basis,
                            'penalty': rule.penalty
                        })
                        
                        # 상세 위반 정보 추가
                        for violation in found_violations:
                            try:
                                detailed_violations.append({
                                    'category': rule.category,
                                    'title': rule.title,
                                    'severity': rule.severity,
                                    'keyword': violation.get('keyword', ''),
                                    'context': violation.get('context', ''),
                                    'position': violation.get('position', 0),
                                    'penalty': rule.penalty,
                                    'legal_basis': rule.legal_basis,
                                    'improvement_guide': rule.improvement_guide,
                                    'full_context': violation.get('full_context', ''),
                                    'sentence_context': violation.get('sentence_context', ''),
                                    'line_number': violation.get('line_number', None),
                                    'paragraph_context': violation.get('paragraph_context', None)
                                })
                            except Exception as e:
                                print(f"상세 위반 정보 추가 중 오류: {e}")
                                continue
                        
                        # 점수 차감 (심각도에 따라)
                        if rule.severity == 'high':
                            total_score -= 25
                        elif rule.severity == 'medium':
                            total_score -= 15
                        else:
                            total_score -= 10
                        
                        # 개선 권장사항 추가
                        try:
                            first_keyword = found_violations[0].get('keyword', '') if found_violations else ''
                            recommendations.append({
                                'category': rule.category,
                                'title': rule.title,
                                'guide': rule.improvement_guide,
                                'priority': 'high' if rule.severity == 'high' else 'medium',
                                'suggested_fixes': self._generate_suggested_fixes(first_keyword, rule) if first_keyword else []
                            })
                        except Exception as e:
                            print(f"권장사항 추가 중 오류: {e}")
                            recommendations.append({
                                'category': rule.category,
                                'title': rule.title,
                                'guide': rule.improvement_guide,
                                'priority': 'high' if rule.severity == 'high' else 'medium',
                                'suggested_fixes': []
                            })
                except Exception as e:
                    print(f"규칙 분석 중 오류: {e}")
                    continue
            
            # 중복 제거 및 통합
            violations = self._remove_duplicate_violations(violations)
            violations = self._consolidate_similar_violations(violations)
            detailed_violations = self._remove_duplicate_detailed_violations(detailed_violations)
            recommendations = self._remove_duplicate_recommendations(recommendations)
            
            # 준수 상태 결정
            if total_score >= 80:
                compliance_status = '적합'
                risk_level = 'low'
            elif total_score >= 60:
                compliance_status = '부분적합'
                risk_level = 'medium'
            else:
                compliance_status = '부적합'
                risk_level = 'high'
            
            # 준수 체크리스트 생성
            try:
                compliance_checklist = self._generate_compliance_checklist(violations, text)
            except Exception as e:
                print(f"체크리스트 생성 중 오류: {e}")
                compliance_checklist = []
            
            # 심의 안내 생성
            try:
                review_guidance = self._generate_review_guidance(violations, text, source_type)
            except Exception as e:
                print(f"심의 안내 생성 중 오류: {e}")
                review_guidance = {}
            
            # 법적 분석
            try:
                legal_analysis = self._analyze_legal_aspects(violations, text, source_type)
            except Exception as e:
                print(f"법적 분석 중 오류: {e}")
                legal_analysis = {
                    'applicable_laws': [],
                    'legal_risks': [],
                    'compliance_requirements': []
                }
            
            # AI 개선 방안 생성
            ai_improvements = []
            if anthropic and detailed_violations:
                try:
                    ai_improvements = self._generate_ai_improvements(detailed_violations, text)
                except Exception as e:
                    print(f"AI 개선 방안 생성 중 오류: {e}")
                    ai_improvements = []
            
            return {
                'overall_score': max(0, total_score),
                'compliance_status': compliance_status,
                'risk_level': risk_level,
                'violations': violations,
                'recommendations': recommendations,
                'detailed_violations': detailed_violations,
                'compliance_checklist': compliance_checklist,
                'review_guidance': review_guidance,
                'extracted_text': text,
                'text_analysis': text_analysis,
                'legal_analysis': legal_analysis,
                'ai_improvements': ai_improvements,
                'summary_report': self._generate_summary_report(violations, total_score, source_type)
            }
        except Exception as e:
            print(f"분석 중 전체 오류: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _analyze_text_quality(self, text: str) -> Dict[str, Any]:
        """텍스트 품질 분석"""
        total_characters = len(text)
        total_words = len(text.split())
        total_sentences = len(re.split(r'[.!?]+', text))
        
        # 텍스트 품질 평가
        if total_characters == 0:
            quality = 'empty'
        elif total_characters < 100:
            quality = 'very_short'
        elif total_characters < 500:
            quality = 'short'
        elif total_characters < 2000:
            quality = 'medium'
        else:
            quality = 'long'
        
        # 문장 구조 분석
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / max(len([s for s in sentences if s.strip()]), 1)
        
        return {
            'total_characters': total_characters,
            'total_words': total_words,
            'total_sentences': total_sentences,
            'text_quality': quality,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'readability_score': self._calculate_readability(text)
        }
    
    def _calculate_readability(self, text: str) -> float:
        """가독성 점수 계산 (간단한 버전)"""
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len([s for s in sentences if s.strip()])
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # 간단한 가독성 공식 (높을수록 읽기 쉬움)
        readability = 100 - (avg_sentence_length * 0.5 + avg_word_length * 2)
        return max(0, min(100, readability))
    
    def _check_rule_violations(self, text: str, rule: ComplianceRule, keywords: List[str]) -> List[Dict]:
        """특정 규칙에 대한 위반 검사"""
        violations = []
        
        # 텍스트를 줄 단위로 분할
        lines = text.split('\n')
        
        for keyword in keywords:
            print(f"[DEBUG] 키워드 '{keyword}' 검색 중...")
            
            # 대소문자 구분 없이 검색
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = list(pattern.finditer(text))
            print(f"[DEBUG] '{keyword}' 매칭 수: {len(matches)}")
            
            for match in matches:
                # 위반 키워드 주변 텍스트 추출 (전후 150자로 확장)
                start = max(0, match.start() - 150)
                end = min(len(text), match.end() + 150)
                context = text[start:end]
                
                # 문장 단위로 확장 (더 정확한 문맥 파악)
                sentence_start = context.rfind('.', 0, 150) + 1
                sentence_end = context.find('.', 150)
                if sentence_end == -1:
                    sentence_end = len(context)
                
                full_context = context[sentence_start:sentence_end].strip()
                if not full_context:
                    full_context = context
                
                print(f"[DEBUG] '{keyword}' 발견! 컨텍스트: {full_context[:100]}...")
                
                # 일반적인 단어 제외 로직을 완화 - 의료광고법에서는 더 엄격하게
                if rule.category in ['환자 후기·경험담', '과장·절대적 표현']:
                    # 환자 후기와 과장 표현은 더 엄격하게 적용
                    pass
                else:
                    # 컨텍스트 기반 위반 여부 재확인
                    if not self._is_actual_violation(keyword, full_context, rule.category):
                        print(f"[DEBUG] '{keyword}' 실제 위반 아님으로 제외")
                        continue
                
                # 정확한 위치 정보 계산
                line_number, column_number = self._find_exact_position(text, match.start(), lines)
                
                # 단락 컨텍스트 찾기
                paragraph_context = self._find_paragraph_context(text, match.start())
                
                # 문단 번호 찾기
                paragraph_number = self._find_paragraph_number(text, match.start())
                
                # 전체 텍스트에서의 위치 비율 계산
                position_percentage = (match.start() / len(text)) * 100
                
                # 문장 내에서의 키워드 위치
                sentence_position = self._find_sentence_position(full_context, keyword)
                
                # 키워드 주변 문맥 (전후 50자)
                immediate_context = self._get_immediate_context(text, match.start(), 50)
                
                violations.append({
                    'keyword': keyword,
                    'context': full_context,
                    'position': match.start(),
                    'full_context': context,
                    'sentence_context': full_context,
                    'line_number': line_number,
                    'column_number': column_number,
                    'paragraph_number': paragraph_number,
                    'paragraph_context': paragraph_context,
                    'exact_location': f"문단 {paragraph_number}, 줄 {line_number}, 열 {column_number}",
                    'highlighted_context': self._highlight_keyword_in_context(full_context, keyword),
                    'suggested_fixes': self._generate_suggested_fixes(keyword, rule),
                    'position_percentage': round(position_percentage, 1),
                    'sentence_position': sentence_position,
                    'immediate_context': immediate_context,
                    'text_position': f"전체 텍스트의 {round(position_percentage, 1)}% 지점",
                    'detailed_location': self._generate_detailed_location(text, match.start(), lines)
                })
        
        return violations
    
    def _find_sentence_position(self, sentence: str, keyword: str) -> str:
        """문장 내에서 키워드의 위치를 찾기"""
        try:
            keyword_pos = sentence.lower().find(keyword.lower())
            if keyword_pos == -1:
                return "문장 중간"
            
            sentence_length = len(sentence)
            if keyword_pos < sentence_length * 0.3:
                return "문장 앞부분"
            elif keyword_pos > sentence_length * 0.7:
                return "문장 뒷부분"
            else:
                return "문장 중간"
        except:
            return "문장 중간"
    
    def _get_immediate_context(self, text: str, position: int, context_length: int = 50) -> str:
        """키워드 주변의 즉시 컨텍스트 추출"""
        start = max(0, position - context_length)
        end = min(len(text), position + context_length)
        return text[start:end].strip()
    
    def _generate_detailed_location(self, text: str, position: int, lines: List[str]) -> str:
        """상세한 위치 정보 생성"""
        # 문단 정보
        paragraphs = text.split('\n\n')
        paragraph_num = 1
        char_count = 0
        for i, paragraph in enumerate(paragraphs):
            if char_count + len(paragraph) + 2 >= position:
                paragraph_num = i + 1
                break
            char_count += len(paragraph) + 2
        
        # 줄 정보
        line_num = 1
        char_count = 0
        for i, line in enumerate(lines):
            if char_count + len(line) >= position:
                line_num = i + 1
                break
            char_count += len(line) + 1
        
        # 위치 비율
        percentage = (position / len(text)) * 100
        
        return f"문단 {paragraph_num}, 줄 {line_num} (전체의 {round(percentage, 1)}% 지점)"
    
    def _is_common_word(self, keyword: str, text: str) -> bool:
        """일반적인 단어인지 확인 (컨텍스트 기반)"""
        # 일반적인 표현들 (광고 목적이 아닌 경우 제외)
        common_expressions = {
            '네이버 블로그': ['네이버 블로그', 'naver blog', '네이버블로그'],
            '네이버': ['네이버', 'naver'],
            '블로그': ['블로그', 'blog'],
            '페이스북': ['페이스북', 'facebook'],
            '인스타그램': ['인스타그램', 'instagram'],
            '유튜브': ['유튜브', 'youtube'],
            '카카오': ['카카오', 'kakao'],
            '구글': ['구글', 'google'],
            '트위터': ['트위터', 'twitter'],
            '틱톡': ['틱톡', 'tiktok'],
            '링크드인': ['링크드인', 'linkedin'],
            '카카오스토리': ['카카오스토리', 'kakao story'],
            '카카오톡': ['카카오톡', 'kakao talk'],
            '텔레그램': ['텔레그램', 'telegram'],
            '라인': ['라인', 'line'],
            '웹사이트': ['웹사이트', 'website'],
            '홈페이지': ['홈페이지', 'homepage'],
            '온라인': ['온라인', 'online'],
            '인터넷': ['인터넷', 'internet'],
            '모바일': ['모바일', 'mobile'],
            '앱': ['앱', 'app'],
            '애플리케이션': ['애플리케이션', 'application']
        }
        
        # 일반적인 표현인지 확인
        for common_expr, variants in common_expressions.items():
            if keyword.lower() in [v.lower() for v in variants]:
                # 단순히 언급만 된 경우는 제외
                if self._is_just_mention(keyword, text):
                    return True
        
        return False
    
    def _is_just_mention(self, keyword: str, text: str) -> bool:
        """단순 언급인지 확인 (광고 목적이 아닌 경우)"""
        # 광고 관련 키워드와 함께 사용되지 않는 경우
        ad_indicators = [
            '광고', '홍보', '선전', '마케팅', '캠페인', '이벤트',
            '할인', '특가', '무료', '증정', '쿠폰', '적립',
            '추천', '소개', '알선', '유인', '모객'
        ]
        
        # 키워드 주변 100자 내에 광고 관련 키워드가 있는지 확인
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        matches = pattern.finditer(text)
        
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            # 광고 관련 키워드가 있으면 실제 위반 가능성
            for indicator in ad_indicators:
                if indicator in context:
                    return False
        
        return True
    
    def _is_actual_violation(self, keyword: str, context: str, category: str) -> bool:
        """실제 위반인지 컨텍스트 기반으로 재확인"""
        # 카테고리별 위반 판단 로직
        if category == 'SNS 미심의 광고':
            # SNS 플랫폼 단순 언급은 제외
            if keyword.lower() in ['네이버', '블로그', '페이스북', '인스타그램', '유튜브']:
                # 광고 목적이 명확한 경우만 위반으로 판단
                ad_indicators = ['광고', '홍보', '선전', '마케팅', '캠페인']
                return any(indicator in context for indicator in ad_indicators)
        
        elif category == '과장·절대적 표현':
            # 의료 효과와 관련된 맥락에서만 위반으로 판단
            medical_indicators = ['치료', '진료', '수술', '시술', '의료', '병원', '의사', '치료법']
            return any(indicator in context for indicator in medical_indicators)
        
        elif category == '환자 후기·경험담':
            # 환자 경험과 관련된 맥락에서만 위반으로 판단
            experience_indicators = ['환자', '치료받은', '수술받은', '경험', '후기', '만족']
            return any(indicator in context for indicator in experience_indicators)
        
        return True
    
    def _find_exact_position(self, text: str, position: int, lines: List[str]) -> Tuple[int, int]:
        """정확한 줄 번호와 열 번호 찾기"""
        char_count = 0
        for i, line in enumerate(lines):
            if char_count + len(line) >= position:
                column_number = position - char_count + 1
                return i + 1, column_number
            char_count += len(line) + 1  # +1 for newline
        return len(lines), 1
    
    def _find_paragraph_number(self, text: str, position: int) -> int:
        """문단 번호 찾기"""
        paragraphs = text.split('\n\n')
        char_count = 0
        for i, paragraph in enumerate(paragraphs):
            if char_count + len(paragraph) + 2 >= position:  # +2 for \n\n
                return i + 1
            char_count += len(paragraph) + 2
        return len(paragraphs)
    
    def _find_paragraph_context(self, text: str, position: int) -> str:
        """위반 위치의 단락 컨텍스트 찾기"""
        # 단락 시작과 끝 찾기
        paragraph_start = position
        paragraph_end = position
        
        # 단락 시작 찾기 (이전 빈 줄까지)
        while paragraph_start > 0:
            if text[paragraph_start-1] == '\n':
                if paragraph_start > 1 and text[paragraph_start-2] == '\n':
                    break
            paragraph_start -= 1
        
        # 단락 끝 찾기 (다음 빈 줄까지)
        while paragraph_end < len(text):
            if text[paragraph_end] == '\n':
                if paragraph_end + 1 < len(text) and text[paragraph_end + 1] == '\n':
                    break
            paragraph_end += 1
        
        return text[paragraph_start:paragraph_end].strip()
    
    def _highlight_keyword_in_context(self, context: str, keyword: str) -> str:
        """컨텍스트에서 키워드를 강조 표시"""
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(f"**{keyword}**", context)
    
    def _generate_suggested_fixes(self, keyword: str, rule: ComplianceRule) -> List[str]:
        """제안 수정사항 생성"""
        fixes = []
        
        # 키워드별 수정 제안
        if '최고' in keyword or '최고의' in keyword:
            fixes.append(f"'{keyword}' → '우수한', '탁월한' 등으로 변경")
        elif '완치' in keyword or '치료' in keyword:
            fixes.append(f"'{keyword}' → '개선', '호전' 등으로 변경")
        elif '보장' in keyword:
            fixes.append(f"'{keyword}' → '도움', '효과' 등으로 변경")
        elif '비교' in keyword:
            fixes.append(f"'{keyword}' → 객관적 사실만 기술")
        elif '후기' in keyword or '경험담' in keyword:
            fixes.append(f"'{keyword}' → 제거 또는 객관적 정보만 포함")
        
        # 일반적인 수정 제안
        fixes.append("과장된 표현을 객관적 사실로 변경")
        fixes.append("절대적 표현을 상대적 표현으로 변경")
        fixes.append("의료적 효과를 보장하는 표현 제거")
        
        return fixes
    
    def _analyze_rule_compliance(self, rule: ComplianceRule, violations: List[Dict], text: str) -> Dict:
        """규칙별 상세 준수 분석"""
        analysis = {
            'compliance_status': 'pass' if len(violations) == 0 else 'fail',
            'violation_details': [],
            'pass_reasons': [],
            'fail_reasons': [],
            'evidence': [],
            'context_analysis': {},
            'keyword_analysis': {},
            'recommendations': []
        }
        
        # 위반 사항 상세 분석
        for violation in violations:
            analysis['violation_details'].append({
                'keyword': violation['keyword'],
                'context': violation['context'],
                'position': violation['position'],
                'severity': rule.severity,
                'legal_basis': rule.legal_basis,
                'penalty': rule.penalty,
                'why_violation': self._explain_violation_reason(violation, rule),
                'suggested_fix': violation['suggested_fixes']
            })
        
        # 통과 사유 분석
        if len(violations) == 0:
            analysis['pass_reasons'] = self._explain_pass_reasons(rule, text)
        
        # 실패 사유 분석
        if len(violations) > 0:
            analysis['fail_reasons'] = self._explain_fail_reasons(violations, rule)
        
        # 증거 및 근거 수집
        analysis['evidence'] = self._collect_compliance_evidence(rule, violations, text)
        
        # 맥락 분석
        analysis['context_analysis'] = self._analyze_text_context(rule, text)
        
        # 키워드 분석
        analysis['keyword_analysis'] = self._analyze_keyword_usage(rule, text)
        
        # 개선 권장사항
        analysis['recommendations'] = self._generate_rule_recommendations(rule, violations, text)
        
        return analysis
    
    def _explain_violation_reason(self, violation: Dict, rule: ComplianceRule) -> str:
        """위반 사유 상세 설명"""
        keyword = violation['keyword']
        category = rule.category
        
        if category == '과장·절대적 표현':
            if '최고' in keyword or '최고의' in keyword:
                return f"'{keyword}'는 의료광고에서 금지되는 절대적 표현입니다. 의료 효과의 우수성을 객관적으로 입증할 수 없어 과장된 표현으로 간주됩니다."
            elif '완치' in keyword or '치료' in keyword:
                return f"'{keyword}'는 의료 효과를 보장하는 표현으로, 의료법상 금지됩니다. 의료 행위의 결과를 보장할 수 없기 때문입니다."
            elif '비교' in keyword:
                return f"'{keyword}'는 객관적 근거 없이 다른 의료기관과 비교하는 표현으로, 공정거래법 위반 소지가 있습니다."
        elif category == '전후사진':
            return f"전후사진 사용 시 의료적 근거와 객관적 비교 기준이 제시되지 않아 과장된 효과로 오인할 수 있습니다."
        elif category == '환자 후기·경험담':
            return f"환자 후기나 경험담은 의료광고에서 활용할 수 없습니다. 개인의 주관적 경험은 객관적 사실이 아니기 때문입니다."
        elif category == 'SNS 미심의 광고':
            return f"SNS 등 10만명 이상 플랫폼에서의 의료광고는 사전심의가 의무입니다. 심의 없이 게시된 광고는 위법합니다."
        
        return f"'{keyword}'는 {rule.legal_basis}에 따라 금지되는 표현입니다."
    
    def _explain_pass_reasons(self, rule: ComplianceRule, text: str) -> List[str]:
        """통과 사유 설명"""
        reasons = []
        
        if rule.category == '과장·절대적 표현':
            if not any(word in text for word in ['최고', '최고의', '완치', '치료', '보장']):
                reasons.append("과장되거나 절대적인 표현이 발견되지 않음")
            if not any(word in text for word in ['비교', '더 나은', '우수한']):
                reasons.append("객관적 근거 없는 비교 표현이 없음")
        
        elif rule.category == '전후사진':
            if '전후' not in text and 'before' not in text.lower() and 'after' not in text.lower():
                reasons.append("전후사진 관련 내용이 없음")
            else:
                reasons.append("전후사진이 있지만 의료적 근거가 제시됨")
        
        elif rule.category == '환자 후기·경험담':
            if not any(word in text for word in ['후기', '경험담', '환자분', '치료받은']):
                reasons.append("환자 후기나 경험담이 포함되지 않음")
        
        elif rule.category == 'SNS 미심의 광고':
            reasons.append("SNS 플랫폼이 아닌 일반 웹사이트 광고로 심의 의무 없음")
        
        reasons.append(f"해당 규칙({rule.title})에 대한 위반 사항이 발견되지 않음")
        
        return reasons
    
    def _explain_fail_reasons(self, violations: List[Dict], rule: ComplianceRule) -> List[str]:
        """실패 사유 설명"""
        reasons = []
        
        for violation in violations:
            keyword = violation['keyword']
            if rule.category == '과장·절대적 표현':
                if '최고' in keyword:
                    reasons.append(f"절대적 표현 '{keyword}' 사용으로 과장 광고 위반")
                elif '완치' in keyword or '치료' in keyword:
                    reasons.append(f"의료 효과 보장 표현 '{keyword}' 사용으로 위반")
            elif rule.category == '전후사진':
                reasons.append("전후사진 사용 시 의료적 근거 미제시")
            elif rule.category == '환자 후기·경험담':
                reasons.append(f"환자 후기/경험담 '{keyword}' 사용으로 위반")
            elif rule.category == 'SNS 미심의 광고':
                reasons.append("SNS 플랫폼에서 사전심의 없이 광고 게시")
        
        return reasons
    
    def _collect_compliance_evidence(self, rule: ComplianceRule, violations: List[Dict], text: str) -> List[Dict]:
        """준수 증거 수집"""
        evidence = []
        
        # 위반 증거
        for violation in violations:
            evidence.append({
                'type': 'violation',
                'keyword': violation['keyword'],
                'context': violation['context'],
                'position': violation['position'],
                'legal_basis': rule.legal_basis
            })
        
        # 준수 증거 (위반이 없는 경우)
        if len(violations) == 0:
            if rule.category == '과장·절대적 표현':
                # 객관적 표현 사용 확인
                objective_words = ['개선', '도움', '효과', '진료', '치료']
                found_objective = [word for word in objective_words if word in text]
                if found_objective:
                    evidence.append({
                        'type': 'compliance',
                        'description': f"객관적 표현 사용: {', '.join(found_objective)}",
                        'legal_basis': rule.legal_basis
                    })
            
            elif rule.category == '전후사진':
                if '전후' not in text:
                    evidence.append({
                        'type': 'compliance',
                        'description': "전후사진 미사용",
                        'legal_basis': rule.legal_basis
                    })
            
            elif rule.category == '환자 후기·경험담':
                if '후기' not in text and '경험담' not in text:
                    evidence.append({
                        'type': 'compliance',
                        'description': "환자 후기/경험담 미사용",
                        'legal_basis': rule.legal_basis
                    })
        
        return evidence
    
    def _analyze_text_context(self, rule: ComplianceRule, text: str) -> Dict:
        """텍스트 맥락 분석"""
        context_analysis = {
            'tone': self._analyze_text_tone(text),
            'subjectivity': self._analyze_subjectivity(text),
            'objectivity_score': self._calculate_objectivity_score(text),
            'medical_terminology': self._extract_medical_terms(text),
            'advertising_elements': self._identify_advertising_elements(text)
        }
        
        return context_analysis
    
    def _analyze_text_tone(self, text: str) -> str:
        """텍스트 톤 분석"""
        promotional_words = ['최고', '최고의', '완벽', '완전', '절대']
        objective_words = ['개선', '도움', '효과', '진료', '치료']
        
        promo_count = sum(1 for word in promotional_words if word in text)
        obj_count = sum(1 for word in objective_words if word in text)
        
        if promo_count > obj_count:
            return 'promotional'
        elif obj_count > promo_count:
            return 'objective'
        else:
            return 'neutral'
    
    def _analyze_subjectivity(self, text: str) -> float:
        """주관성 분석 (0-1, 1이 가장 주관적)"""
        subjective_words = ['최고', '완벽', '완전', '절대', '보장', '확실']
        objective_words = ['개선', '도움', '효과', '진료', '치료', '진행']
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        subj_count = sum(1 for word in subjective_words if word in text)
        obj_count = sum(1 for word in objective_words if word in text)
        
        if subj_count + obj_count == 0:
            return 0.5
        
        return subj_count / (subj_count + obj_count)
    
    def _calculate_objectivity_score(self, text: str) -> float:
        """객관성 점수 계산 (0-100)"""
        subjectivity = self._analyze_subjectivity(text)
        return (1 - subjectivity) * 100
    
    def _extract_medical_terms(self, text: str) -> List[str]:
        """의료 용어 추출"""
        medical_terms = [
            '진료', '치료', '진단', '수술', '시술', '처방', '약물',
            '증상', '질환', '병원', '의원', '클리닉', '의료진',
            '개선', '호전', '완화', '예방', '관리'
        ]
        
        found_terms = [term for term in medical_terms if term in text]
        return found_terms
    
    def _identify_advertising_elements(self, text: str) -> List[str]:
        """광고 요소 식별"""
        ad_elements = []
        
        if any(word in text for word in ['연락처', '전화', '문의', '상담']):
            ad_elements.append('연락처 정보')
        
        if any(word in text for word in ['위치', '주소', '오시는 길']):
            ad_elements.append('위치 정보')
        
        if any(word in text for word in ['진료시간', '운영시간', '예약']):
            ad_elements.append('진료 정보')
        
        if any(word in text for word in ['전문의', '의료진', '경력']):
            ad_elements.append('의료진 정보')
        
        return ad_elements
    
    def _analyze_keyword_usage(self, rule: ComplianceRule, text: str) -> Dict:
        """키워드 사용 분석"""
        try:
            keywords = self.keywords.get(rule.category, [])
        except:
            keywords = []
        
        analysis = {
            'total_keywords': len(keywords),
            'found_keywords': [],
            'keyword_frequency': {},
            'context_analysis': {}
        }
        
        try:
            for keyword in keywords:
                if keyword in text:
                    analysis['found_keywords'].append(keyword)
                    count = text.count(keyword)
                    analysis['keyword_frequency'][keyword] = count
                    
                    # 키워드 맥락 분석
                    try:
                        context = self._find_keyword_context(text, keyword)
                        analysis['context_analysis'][keyword] = {
                            'context': context,
                            'usage_type': self._classify_keyword_usage(keyword, context)
                        }
                    except Exception as e:
                        analysis['context_analysis'][keyword] = {
                            'context': '',
                            'usage_type': '일반 표현'
                        }
        except Exception as e:
            # 오류 발생 시 기본값 반환
            pass
        
        return analysis
    
    def _find_keyword_context(self, text: str, keyword: str) -> str:
        """키워드 맥락 찾기"""
        try:
            index = text.index(keyword)
            start = max(0, index - 50)
            end = min(len(text), index + len(keyword) + 50)
            return text[start:end]
        except ValueError:
            return ""
    
    def _classify_keyword_usage(self, keyword: str, context: str) -> str:
        """키워드 사용 유형 분류"""
        if '최고' in keyword or '완벽' in keyword:
            return '절대적 표현'
        elif '완치' in keyword or '치료' in keyword:
            return '효과 보장'
        elif '비교' in keyword:
            return '비교 광고'
        elif '후기' in keyword or '경험담' in keyword:
            return '환자 후기'
        else:
            return '일반 표현'
    
    def _generate_rule_recommendations(self, rule: ComplianceRule, violations: List[Dict], text: str) -> List[str]:
        """규칙별 개선 권장사항 생성"""
        recommendations = []
        
        if len(violations) > 0:
            for violation in violations:
                keyword = violation['keyword']
                if '최고' in keyword:
                    recommendations.append(f"'{keyword}' → '우수한', '전문적인' 등으로 변경")
                elif '완치' in keyword:
                    recommendations.append(f"'{keyword}' → '개선', '호전' 등으로 변경")
                elif '보장' in keyword:
                    recommendations.append(f"'{keyword}' → '도움', '효과' 등으로 변경")
                elif '비교' in keyword:
                    recommendations.append("객관적 근거를 제시하거나 비교 표현 제거")
                elif '후기' in keyword or '경험담' in keyword:
                    recommendations.append("환자 후기/경험담 제거하고 객관적 정보만 포함")
        else:
            recommendations.append(f"현재 {rule.title} 규칙을 잘 준수하고 있습니다.")
            recommendations.append("지속적인 모니터링을 통해 규정 준수를 유지하세요.")
        
        return recommendations
    
    def _calculate_rule_compliance_score(self, rule: ComplianceRule, violations: List[Dict], text: str) -> int:
        """규칙별 준수 점수 계산 (0-100)"""
        if len(violations) == 0:
            return 100
        
        # 위반 심각도에 따른 점수 차감
        total_deduction = 0
        for violation in violations:
            if rule.severity == 'high':
                total_deduction += 30
            elif rule.severity == 'medium':
                total_deduction += 20
            else:
                total_deduction += 10
        
        # 위반 횟수에 따른 추가 차감
        violation_penalty = len(violations) * 5
        
        score = max(0, 100 - total_deduction - violation_penalty)
        return score
    
    def _generate_compliance_checklist(self, violations: List[Dict], text: str) -> List[Dict]:
        """준수 체크리스트 생성 - keyword 접근을 get으로 변경"""
        checklist = []
        
        # 모든 규칙에 대해 체크리스트 항목 생성
        for rule in self.rules:
            # violations에는 category 정보가 없으므로 rule별로 필터링하지 않음
            rule_violations = violations  # 임시로 모든 violations 사용
            has_violation = len(rule_violations) > 0
            
            # 해당 규칙에 대한 상세 분석
            detailed_analysis = self._analyze_rule_compliance(rule, rule_violations, text)
            
            checklist.append({
                'category': rule.category,
                'title': rule.title,
                'description': rule.description,
                'status': 'pass' if not has_violation else 'fail',
                'severity': rule.severity,
                'legal_basis': rule.legal_basis,
                'check_items': self._generate_check_items(rule),
                'detailed_analysis': detailed_analysis,
                'violation_count': len(rule_violations),
                'compliance_score': self._calculate_rule_compliance_score(rule, rule_violations, text)
            })
        
        return checklist
    
    def _generate_check_items(self, rule: ComplianceRule) -> List[Dict]:
        """체크리스트 세부 항목 생성"""
        check_items = []
        
        # 규칙 카테고리별 체크 항목
        if rule.category == '과장·절대적 표현':
            check_items = [
                {'item': '최고, 최고의 표현 사용 여부', 'required': True},
                {'item': '완치, 치료 보장 표현 사용 여부', 'required': True},
                {'item': '비교 광고 시 객관적 근거 제시 여부', 'required': True},
                {'item': '과장된 효과 표현 사용 여부', 'required': True}
            ]
        elif rule.category == '전후사진':
            check_items = [
                {'item': '전후사진 사용 시 의료적 근거 제시 여부', 'required': True},
                {'item': '과도한 보정 및 조작 여부', 'required': True},
                {'item': '객관적 비교 기준 제시 여부', 'required': True}
            ]
        elif rule.category == '환자 후기·경험담':
            check_items = [
                {'item': '환자 후기 사용 여부', 'required': False},
                {'item': '경험담 광고 활용 여부', 'required': False},
                {'item': '객관적 정보만 포함 여부', 'required': True}
            ]
        else:
            check_items = [
                {'item': '규정 준수 여부', 'required': True},
                {'item': '객관적 사실 기반 여부', 'required': True}
            ]
        
        return check_items
    
    def _generate_review_guidance(self, violations: List[Dict], text: str, source_type: str) -> Dict:
        """심의 안내 생성"""
        guidance = {
            'requires_review': False,
            'review_type': None,
            'review_fee': None,
            'review_process': None,
            'submission_requirements': [],
            'notes': [],
            'submission_restrictions': [],
            'legal_basis': [],
            'penalties': [],
            'deadline': None,
            'contact_info': {}
        }
        
        # SNS 관련 위반이 있는지 확인 (임시로 모든 violations 사용)
        sns_violations = violations  # 임시로 모든 violations 사용
        
        # 의료광고 범주 외 위반 확인 (임시로 빈 리스트)
        category_violations = []
        
        # 수정사항 과다 위반 확인 (임시로 빈 리스트)
        excessive_modifications = []
        
        # 심의 필요성 판단
        if sns_violations or len(violations) >= 3:
            guidance['requires_review'] = True
            guidance['review_type'] = '사전심의'
            guidance['review_fee'] = '50,000원'
            guidance['deadline'] = '심의일 1주일 전'
            
            if source_type == 'sns':
                guidance['notes'].append('SNS 등 10만명 이상 플랫폼 광고는 사전심의 의무')
                guidance['legal_basis'].append('의료광고법 제6조')
            else:
                guidance['notes'].append('3개 이상 위반사항 발견으로 사전심의 권장')
        
        # 심의 절차 안내
        if guidance['requires_review']:
            guidance['review_process'] = [
                '1. 심의 신청서 작성',
                '2. 광고물 첨부',
                '3. 심의비 납부',
                '4. 심의위원회 검토',
                '5. 심의 결과 통보'
            ]
            
            guidance['submission_requirements'] = [
                '심의 신청서 1부',
                '광고물 원본',
                '심의비 납부증',
                '추가 설명서 (필요시)'
            ]
            
            guidance['contact_info'] = {
                'medical': {
                    'name': '대한의사협회 의료광고심의위원회',
                    'phone': '02-6350-6666',
                    'email': 'adreview@kma.org',
                    'address': '서울특별시 종로구 창성동 7-1'
                },
                'dental': {
                    'name': '치과의사협회 치과의료광고심의위원회',
                    'phone': '02-6350-6666',
                    'email': 'dental@kda.or.kr',
                    'address': '서울특별시 종로구 창성동 7-1'
                }
            }
        
        # 처벌 기준 안내 (임시로 기본값 사용)
        if violations:
            guidance['penalties'].append({
                'type': '과태료',
                'amount': '1,000만원 이하',
                'basis': '의료법 제27조'
            })
        
        return guidance
    
    def _analyze_legal_aspects(self, violations: List[Dict], text: str, source_type: str) -> Dict:
        """법적 측면 분석"""
        legal_analysis = {
            'applicable_laws': [],
            'legal_risks': [],
            'compliance_requirements': [],
            'regulatory_updates': [],
            'case_law': []
        }
        
        # 적용 가능한 법령
        legal_analysis['applicable_laws'] = [
            {
                'law': '의료법',
                'articles': ['제27조', '제56조', '제57조', '제57조의2'],
                'description': '의료광고의 기본 원칙과 제한사항'
            },
            {
                'law': '의료광고법',
                'articles': ['제6조', '제7조', '제8조'],
                'description': '의료광고 심의 및 처벌 규정'
            },
            {
                'law': '공정거래위원회 고시',
                'articles': ['의료광고 심의기준'],
                'description': '의료광고 심의 세부 기준'
            }
        ]
        
        # 법적 위험 요소
        for violation in violations:
            # violation이 딕셔너리인지 확인하고 안전하게 접근
            if isinstance(violation, dict):
                legal_analysis['legal_risks'].append({
                    'risk_type': violation.get('category', '알 수 없음'),
                    'severity': violation.get('severity', 'medium'),
                    'legal_basis': violation.get('legal_basis', ''),
                    'potential_penalty': violation.get('penalty', ''),
                    'mitigation': self._suggest_legal_mitigation(violation)
                })
        
        # 준수 요구사항
        legal_analysis['compliance_requirements'] = [
            '의료광고는 객관적 사실에 근거해야 함',
            '과장된 표현 사용 금지',
            '절대적 표현 사용 금지',
            '환자 후기·경험담 광고 활용 금지',
            '전후사진 사용 시 의료적 근거 제시',
            'SNS 등 10만명 이상 플랫폼 광고 시 사전심의 의무'
        ]
        
        # 최신 규제 업데이트
        legal_analysis['regulatory_updates'] = [
            {
                'date': '2025년 1월',
                'update': 'SNS 등 10만명 이상 플랫폼 광고 사전심의 의무화',
                'impact': 'high'
            },
            {
                'date': '2025년 1월',
                'update': '환자 후기·경험담 광고 활용 전면 금지 강화',
                'impact': 'high'
            },
            {
                'date': '2025년 1월',
                'update': '신의료기술 미평가 시술 광고 금지',
                'impact': 'medium'
            }
        ]
        
        return legal_analysis
    
    def _suggest_legal_mitigation(self, violation: Dict) -> str:
        """법적 위험 완화 방안 제안"""
        category = violation.get('category', '')
        if category == '과장·절대적 표현':
            return "객관적 사실에 근거한 표현으로 수정, 절대적 표현 제거"
        elif category == '전후사진':
            return "의료적 근거 제시, 객관적 비교 기준 명시"
        elif category == '환자 후기·경험담':
            return "환자 후기 제거, 객관적 정보만 포함"
        else:
            return "해당 규정에 맞게 수정"
    
    def _generate_summary_report(self, violations: List[Dict], total_score: int, source_type: str) -> Dict:
        """요약 리포트 생성"""
        # 안전하게 위반 사항 분석
        high_severity = len([v for v in violations if isinstance(v, dict) and v.get('severity') == 'high'])
        medium_severity = len([v for v in violations if isinstance(v, dict) and v.get('severity') == 'medium'])
        low_severity = len([v for v in violations if isinstance(v, dict) and v.get('severity') == 'low'])
        
        return {
            'executive_summary': {
                'total_violations': len(violations),
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity,
                'compliance_score': total_score,
                'risk_assessment': 'high' if total_score < 60 else 'medium' if total_score < 80 else 'low'
            },
            'key_findings': [
                f"{len(violations)}개의 위반사항 발견",
                f"준수도 점수: {total_score}/100",
                f"심각도 높은 위반: {high_severity}개"
            ],
            'immediate_actions': [
                "과장된 표현 수정",
                "절대적 표현 제거",
                "객관적 사실 기반으로 재작성"
            ] if violations else ["현재 상태 유지"],
            'long_term_recommendations': [
                "의료광고법 정기 교육 참여",
                "심의 기준 정기 업데이트 확인",
                "내부 검토 프로세스 구축"
            ]
        }
    
    def get_recommended_expressions(self, category: str = None) -> List[Dict]:
        """권장 표현 조회"""
        if category:
            return [expr for expr in self.recommended_expressions if expr['category'] == category]
        return self.recommended_expressions
    
    def get_rule_details(self, category: str) -> Dict:
        """규칙 상세 정보 조회"""
        for rule in self.rules:
            if rule.category == category:
                return {
                    'title': rule.title,
                    'description': rule.description,
                    'legal_basis': rule.legal_basis,
                    'penalty': rule.penalty,
                    'improvement_guide': rule.improvement_guide,
                    'keywords': self.keywords.get(category, [])
                }
        return {}
    
    def _generate_ai_improvements(self, detailed_violations: List[Dict], original_text: str) -> List[Dict]:
        """Claude API를 사용하여 위반 항목에 대한 AI 개선 방안 생성"""
        if not anthropic:
            return []
        
        ai_improvements = []
        
        # 상위 3개 위반 항목에 대해서만 AI 개선 방안 생성 (API 비용 절약)
        for violation in detailed_violations[:3]:
            try:
                improvement = self._get_ai_improvement_suggestion(violation, original_text)
                if improvement:
                    ai_improvements.append(improvement)
            except Exception as e:
                print(f"개별 위반 항목 AI 개선 방안 생성 중 오류: {e}")
                continue
        
        return ai_improvements
    
    def _get_ai_improvement_suggestion(self, violation: Dict, original_text: str) -> Dict:
        """개별 위반 항목에 대한 AI 개선 방안 생성"""
        try:
            # 위반 정보 구성
            violation_info = {
                'category': violation.get('category', ''),
                'keyword': violation.get('keyword', ''),
                'context': violation.get('context', ''),
                'legal_basis': violation.get('legal_basis', ''),
                'penalty': violation.get('penalty', '')
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
    "title": "개선 방안 제목",
    "description": "구체적인 개선 방안 설명",
    "improved_keyword": "대체 키워드",
    "improved_sentence": "개선된 문장",
    "alternative_expressions": ["대안 표현 1", "대안 표현 2"],
    "additional_recommendations": ["추가 권장사항 1", "추가 권장사항 2"],
    "legal_compliance_notes": "법적 준수 관련 참고사항"
}}
"""
            
            # Claude API 호출
            response = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
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
                    # JSON이 없으면 기본 구조로 생성
                    suggestions = {
                        'title': f"{violation_info['category']} 개선 방안",
                        'description': content,
                        'improved_keyword': '대체 표현',
                        'improved_sentence': content,
                        'alternative_expressions': [],
                        'additional_recommendations': [],
                        'legal_compliance_notes': 'AI가 제안한 개선 방안입니다.'
                    }
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 구조로 생성
                suggestions = {
                    'title': f"{violation_info['category']} 개선 방안",
                    'description': content,
                    'improved_keyword': '대체 표현',
                    'improved_sentence': content,
                    'alternative_expressions': [],
                    'alternative_expressions': [],
                    'additional_recommendations': [],
                    'legal_compliance_notes': 'AI가 제안한 개선 방안입니다.'
                }
            
            return {
                'violation_category': violation_info['category'],
                'violation_keyword': violation_info['keyword'],
                'suggestions': suggestions,
                'raw_response': content
            }
            
        except Exception as e:
            print(f"AI 개선 방안 생성 중 오류: {e}")
            return None 
    
    def _remove_duplicate_violations(self, violations: List[Dict]) -> List[Dict]:
        """중복된 위반 항목 제거"""
        seen = set()
        unique_violations = []
        
        for violation in violations:
            # 카테고리와 제목으로 중복 판단
            key = (violation.get('category', ''), violation.get('title', ''))
            if key not in seen:
                seen.add(key)
                unique_violations.append(violation)
        
        return unique_violations
    
    def _remove_duplicate_detailed_violations(self, detailed_violations: List[Dict]) -> List[Dict]:
        """중복된 상세 위반 항목 제거"""
        seen = set()
        unique_violations = []
        
        for violation in detailed_violations:
            # 카테고리, 제목, 키워드, 위치로 중복 판단
            key = (
                violation.get('category', ''),
                violation.get('title', ''),
                violation.get('keyword', ''),
                violation.get('position', 0)
            )
            if key not in seen:
                seen.add(key)
                unique_violations.append(violation)
        
        return unique_violations
    
    def _remove_duplicate_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """중복된 권장사항 제거"""
        seen = set()
        unique_recommendations = []
        
        for recommendation in recommendations:
            # 카테고리와 제목으로 중복 판단
            key = (recommendation.get('category', ''), recommendation.get('title', ''))
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(recommendation)
        
        return unique_recommendations
    
    def _consolidate_similar_violations(self, violations: List[Dict]) -> List[Dict]:
        """유사한 위반 항목 통합"""
        consolidated = {}
        
        for violation in violations:
            category = violation.get('category', '')
            title = violation.get('title', '')
            key = (category, title)
            
            if key in consolidated:
                # 기존 위반 항목에 카운트 추가
                consolidated[key]['count'] += violation.get('count', 1)
                # 더 심각한 위험도로 업데이트
                if violation.get('severity') == 'high':
                    consolidated[key]['severity'] = 'high'
                elif violation.get('severity') == 'medium' and consolidated[key]['severity'] != 'high':
                    consolidated[key]['severity'] = 'medium'
            else:
                consolidated[key] = violation.copy()
        
        return list(consolidated.values()) 