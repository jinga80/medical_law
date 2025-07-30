import PyPDF2
import docx
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
import io
import re
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(uploaded_file):
    """업로드된 파일에서 텍스트 추출"""
    try:
        file_content = uploaded_file.read()
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.pdf'):
            return TextExtractor.extract_from_pdf(file_content)
        elif file_name.endswith(('.docx', '.doc')):
            return TextExtractor.extract_from_docx(file_content)
        elif file_name.endswith('.txt'):
            return TextExtractor.extract_from_txt(file_content)
        else:
            raise ValueError('지원하지 않는 파일 형식입니다. (PDF, Word, 텍스트 파일만 지원)')
    except Exception as e:
        logger.error(f"파일 텍스트 추출 실패: {e}")
        raise ValueError(f"파일에서 텍스트를 추출할 수 없습니다: {str(e)}")

class TextExtractor:
    """텍스트 추출 클래스"""
    
    @staticmethod
    def extract_from_pdf(file_content):
        """PDF에서 텍스트 추출"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
            raise ValueError("PDF에서 텍스트를 추출할 수 없습니다. 이미지 기반 PDF이거나 보호된 파일일 수 있습니다.")
    
    @staticmethod
    def extract_from_docx(file_content):
        """Word 문서에서 텍스트 추출"""
        try:
            doc = docx.Document(io.BytesIO(file_content))
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Word 텍스트 추출 실패: {e}")
            raise ValueError("Word 문서에서 텍스트를 추출할 수 없습니다.")
    
    @staticmethod
    def extract_from_txt(file_content):
        """텍스트 파일에서 텍스트 추출"""
        try:
            # UTF-8로 디코딩 시도
            text = file_content.decode('utf-8')
            return text.strip()
        except UnicodeDecodeError:
            try:
                # CP949로 디코딩 시도 (한글 Windows)
                text = file_content.decode('cp949')
                return text.strip()
            except UnicodeDecodeError:
                raise ValueError("텍스트 파일의 인코딩을 인식할 수 없습니다.")

class WebTextExtractor:
    """웹 페이지에서 텍스트 추출 클래스"""
    
    @staticmethod
    def extract_from_url(url, simple_mode=False):
        """URL에서 본문 텍스트 추출 (simple_mode: 자바스크립트 무시, body 전체 텍스트 복사)"""
        try:
            # simple_mode면 requests로 받아온 body 전체 텍스트만 반환
            if simple_mode:
                return WebTextExtractor._extract_simple_text(url)
            # 먼저 requests로 시도
            text = WebTextExtractor._extract_with_requests(url)
            if text:
                return text
            # 실패하면 Selenium으로 시도
            return WebTextExtractor._extract_with_selenium(url)
        except Exception as e:
            logger.error(f"URL 텍스트 추출 실패: {e}")
            raise ValueError(f"URL에서 텍스트를 추출할 수 없습니다: {str(e)}")

    @staticmethod
    def _extract_simple_text(url):
        """자바스크립트 무시, body 전체 + 주요 블록 태그 + meta/title/og:description까지 최대한 텍스트 복사"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # 응답이 HTML인지 확인
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                return f"URL에서 HTML 콘텐츠를 찾을 수 없습니다. Content-Type: {content_type}"
            
            soup = BeautifulSoup(response.content, 'html.parser')

            # 1. script/style/meta/link 등 제거
            for element in soup(['script', 'style', 'link', 'noscript']):
                element.decompose()

            # 2. 숨겨진 요소(스타일, 속성 등) 제거
            for tag in soup.find_all(True):
                style = tag.get('style', '')
                if 'display:none' in style or 'visibility:hidden' in style:
                    tag.decompose()
                if tag.has_attr('hidden') or tag.get('aria-hidden') == 'true':
                    tag.decompose()

            # 3. 주요 블록 태그 텍스트 수집
            block_tags = ['p', 'div', 'span', 'li', 'section', 'article', 'table', 'header', 'footer', 'aside', 'main']
            block_texts = []
            for tag in block_tags:
                for elem in soup.find_all(tag):
                    txt = elem.get_text(separator=' ', strip=True)
                    if txt and len(txt) > 10:
                        block_texts.append(txt)

            # 4. body 전체 텍스트
            body = soup.body
            body_text = body.get_text(separator=' ', strip=True) if body else ''

            # 5. 네이버 블로그 특화 처리
            if 'blog.naver.com' in url:
                # 네이버 블로그는 더 깊은 구조 탐색
                blog_selectors = [
                    '.se-main-container', '.post_content', '#postViewArea',
                    '.se-component', '.se-text-paragraph', '.se-text',
                    '.se-image-caption', '.se-caption'
                ]
                for selector in blog_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and len(text) > 5:
                            block_texts.append(text)
                
                # 깊은 div 구조 추가 탐색 (XPath 스타일)
                deep_divs = soup.find_all('div', recursive=True)
                for div in deep_divs:
                    text = div.get_text(strip=True)
                    if text and len(text) > 20:
                        block_texts.append(text)
                
                # table 구조 탐색
                tables = soup.find_all('table')
                for table in tables:
                    text = table.get_text(strip=True)
                    if text and len(text) > 10:
                        block_texts.append(text)
            
            # 6. meta, title, og:description 등 SEO 텍스트
            meta_texts = []
            if soup.title and soup.title.string:
                meta_texts.append(soup.title.string.strip())
            for meta in soup.find_all('meta'):
                if meta.get('name') in ['description', 'keywords'] and meta.get('content'):
                    meta_texts.append(meta['content'].strip())
                if meta.get('property') in ['og:description', 'og:title'] and meta.get('content'):
                    meta_texts.append(meta['content'].strip())

            # 6. 모든 텍스트 합치기 (중복 제거) - iframe 제거로 안정성 향상
            all_texts = meta_texts + [body_text] + block_texts
            # 중복 제거, 길이순 정렬(긴 것 우선)
            seen = set()
            unique_texts = []
            for t in all_texts:
                t_norm = re.sub(r'\s+', ' ', t.strip())
                if t_norm and t_norm not in seen:
                    seen.add(t_norm)
                    unique_texts.append(t_norm)
            # 한 줄로 합치되, 너무 길면 줄바꿈 추가
            result = '\n\n'.join(unique_texts)
            # 최종 공백 정리
            result = re.sub(r'\n{3,}', '\n\n', result)
            result = re.sub(r'\s{3,}', '  ', result)
            return result.strip()
        except Exception as e:
            logger.warning(f"simple_mode 텍스트 추출 실패: {e}")
            return f"URL에서 텍스트를 추출할 수 없습니다: {str(e)}"

    @staticmethod
    def _extract_with_requests(url):
        """requests를 사용한 텍스트 추출"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # iframe이 있는지 확인
            iframes = soup.find_all('iframe')
            if iframes:
                logger.info(f"iframe 발견: {len(iframes)}개")
                return WebTextExtractor._extract_from_iframes(iframes, url)
            
            # 불필요한 요소 제거
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # 특정 웹사이트별 특별 처리
            if 'blog.naver.com' in url:
                return WebTextExtractor._extract_naver_blog(soup)
            elif 'facebook.com' in url:
                return WebTextExtractor._extract_facebook(soup)
            elif 'instagram.com' in url:
                return WebTextExtractor._extract_instagram(soup)
            elif 'youtube.com' in url or 'youtu.be' in url:
                return WebTextExtractor._extract_youtube(soup)
            elif 'tistory.com' in url:
                return WebTextExtractor._extract_tistory(soup)
            elif 'brunch.co.kr' in url:
                return WebTextExtractor._extract_brunch(soup)
            elif 'medium.com' in url:
                return WebTextExtractor._extract_medium(soup)
            else:
                return WebTextExtractor._extract_general_content(soup)
                
        except Exception as e:
            logger.warning(f"requests 추출 실패: {e}")
            return None
    
    @staticmethod
    def _extract_with_selenium(url):
        """Selenium을 사용한 텍스트 추출 (JavaScript 렌더링 필요)"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # 페이지 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # iframe이 있는지 확인
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                logger.info(f"Selenium에서 iframe 발견: {len(iframes)}개")
                text = WebTextExtractor._extract_from_iframes_selenium(driver, iframes, url)
                if text:
                    driver.quit()
                    return text.strip()
            
            # 특정 웹사이트별 특별 처리 (Selenium)
            if 'blog.naver.com' in url:
                text = WebTextExtractor._extract_naver_blog_selenium(driver)
            elif 'instagram.com' in url:
                text = WebTextExtractor._extract_instagram_selenium(driver)
            elif 'youtube.com' in url or 'youtu.be' in url:
                text = WebTextExtractor._extract_youtube_selenium(driver)
            elif 'tistory.com' in url:
                text = WebTextExtractor._extract_tistory_selenium(driver)
            else:
                text = driver.find_element(By.TAG_NAME, "body").text
            
            driver.quit()
            return text.strip()
            
        except Exception as e:
            logger.error(f"Selenium 추출 실패: {e}")
            if 'driver' in locals():
                driver.quit()
            raise
    
    @staticmethod
    def _extract_naver_blog(soup):
        """네이버 블로그 본문 추출 (강화된 버전)"""
        all_texts = []
        
        # 1. 기존 선택자들로 시도
        selectors = [
            '.se-main-container',  # 새 에디터
            '.post_content',       # 구 에디터
            '#postViewArea',       # 구 에디터
            '.se-component',       # 새 에디터 컴포넌트
            '.se-text-paragraph',  # 새 에디터 텍스트
            '.se-text',           # 새 에디터 텍스트
            '.se-image-caption',   # 이미지 캡션
            '.se-caption',        # 캡션
        ]
        
        for selector in selectors:
            contents = soup.select(selector)
            for content in contents:
                # 불필요한 요소 제거
                for element in content(['script', 'style', 'iframe']):
                    element.decompose()
                text = content.get_text(strip=True)
                if text and len(text) > 10:
                    all_texts.append(text)
        
        # 2. 깊은 div 구조 탐색 (XPath 스타일 접근)
        # div[7]부터 시작하는 깊은 구조 탐색
        deep_divs = soup.find_all('div', recursive=True)
        for div in deep_divs:
            # 텍스트가 있는 div만 선택
            if div.get_text(strip=True) and len(div.get_text(strip=True)) > 20:
                # 불필요한 요소 제거
                for element in div(['script', 'style', 'iframe', 'nav', 'header', 'footer']):
                    element.decompose()
                text = div.get_text(strip=True)
                if text and len(text) > 20:
                    all_texts.append(text)
        
        # 3. table 구조 탐색 (XPath에서 table[2] 등)
        tables = soup.find_all('table')
        for table in tables:
            text = table.get_text(strip=True)
            if text and len(text) > 10:
                all_texts.append(text)
        
        # 4. span 요소들 탐색 (XPath에서 span[2] 등)
        spans = soup.find_all('span')
        for span in spans:
            text = span.get_text(strip=True)
            if text and len(text) > 10:
                all_texts.append(text)
        
        # 5. 모든 텍스트 블록 수집 (더 포괄적)
        text_elements = soup.find_all(['p', 'div', 'span', 'td', 'th', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for elem in text_elements:
            text = elem.get_text(strip=True)
            if text and len(text) > 5:
                all_texts.append(text)
        
        # 6. 중복 제거 및 정리
        seen = set()
        unique_texts = []
        for text in all_texts:
            text_norm = re.sub(r'\s+', ' ', text.strip())
            if text_norm and text_norm not in seen and len(text_norm) > 5:
                seen.add(text_norm)
                unique_texts.append(text_norm)
        
        if unique_texts:
            return '\n\n'.join(unique_texts)
        
        # 7. 마지막 수단으로 일반적인 본문 영역 시도
        return WebTextExtractor._extract_general_content(soup)
    
    @staticmethod
    def _extract_naver_blog_selenium(driver):
        """Selenium으로 네이버 블로그 본문 추출 (강화된 버전)"""
        all_texts = []
        
        # 1. 기존 선택자들로 시도
        selectors = [
            '.se-main-container',
            '.post_content',
            '#postViewArea',
            '.se-component',
            '.se-text-paragraph',
            '.se-text',
            '.se-image-caption',
            '.se-caption',
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 10:
                        all_texts.append(text)
            except:
                continue
        
        # 2. 깊은 div 구조 탐색
        try:
            # 모든 div 요소 찾기
            divs = driver.find_elements(By.TAG_NAME, "div")
            for div in divs:
                try:
                    text = div.text.strip()
                    if text and len(text) > 20:
                        all_texts.append(text)
                except:
                    continue
        except:
            pass
        
        # 3. table 구조 탐색
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                try:
                    text = table.text.strip()
                    if text and len(text) > 10:
                        all_texts.append(text)
                except:
                    continue
        except:
            pass
        
        # 4. span 요소들 탐색
        try:
            spans = driver.find_elements(By.TAG_NAME, "span")
            for span in spans:
                try:
                    text = span.text.strip()
                    if text and len(text) > 10:
                        all_texts.append(text)
                except:
                    continue
        except:
            pass
        
        # 5. 중복 제거 및 정리
        seen = set()
        unique_texts = []
        for text in all_texts:
            text_norm = re.sub(r'\s+', ' ', text.strip())
            if text_norm and text_norm not in seen and len(text_norm) > 5:
                seen.add(text_norm)
                unique_texts.append(text_norm)
        
        if unique_texts:
            return '\n\n'.join(unique_texts)
        
        # 6. 마지막 수단으로 body 전체 텍스트
        try:
            return driver.find_element(By.TAG_NAME, "body").text
        except:
            return ""
    
    @staticmethod
    def _extract_facebook(soup):
        """페이스북 본문 추출"""
        # 페이스북 포스트 본문 선택자들
        selectors = [
            '[data-testid="post_message"]',
            '.userContent',
            '.post_content',
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)
        
        return WebTextExtractor._extract_general_content(soup)
    
    @staticmethod
    def _extract_instagram(soup):
        """인스타그램 본문 추출"""
        # 인스타그램 포스트 본문 선택자들
        selectors = [
            'article div[data-testid="post-caption"]',
            '.caption',
            '.post-caption',
            '[data-testid="post-caption"]',
            'article div[dir="auto"]'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)
        
        return WebTextExtractor._extract_general_content(soup)
    
    @staticmethod
    def _extract_youtube(soup):
        """유튜브 본문 추출"""
        # 유튜브 동영상 설명 선택자들
        selectors = [
            '#description',
            '.description',
            '#meta-contents',
            '.ytd-video-secondary-info-renderer'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)
        
        return WebTextExtractor._extract_general_content(soup)
    
    @staticmethod
    def _extract_tistory(soup):
        """티스토리 블로그 본문 추출"""
        # 티스토리 본문 선택자들
        selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.entry',
            '.post',
            '#entry'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                # 불필요한 요소 제거
                for element in content(['script', 'style', '.revenue_unit_wrap', '.adsbygoogle']):
                    element.decompose()
                return content.get_text(strip=True)
        
        return WebTextExtractor._extract_general_content(soup)
    
    @staticmethod
    def _extract_brunch(soup):
        """브런치 본문 추출"""
        # 브런치 본문 선택자들
        selectors = [
            '.wrap_body',
            '.body',
            '.article-body',
            '.post-body'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)
        
        return WebTextExtractor._extract_general_content(soup)
    
    @staticmethod
    def _extract_medium(soup):
        """미디엄 본문 추출"""
        # 미디엄 본문 선택자들
        selectors = [
            'article',
            '.postArticle-content',
            '.section-content',
            '.story-content'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)
        
        return WebTextExtractor._extract_general_content(soup)
    
    @staticmethod
    def _extract_general_content(soup):
        """일반적인 웹페이지 본문 추출 (개선된 버전)"""
        # 본문으로 추정되는 요소들 (우선순위 순)
        content_selectors = [
            'main',
            'article',
            '.main-content',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.post-body',
            '.entry-body',
            '#content',
            '.container',
            '.wrapper'
        ]
        
        # 각 선택자로 본문 찾기
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                # 불필요한 요소 제거
                for element in content(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'button']):
                    element.decompose()
                
                text = content.get_text(strip=True)
                if len(text) > 100:  # 의미있는 텍스트가 있는지 확인
                    return text
        
        # 본문을 찾지 못한 경우 p 태그들만 추출
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            if len(text) > 50:
                return text
        
        # 마지막 수단으로 body 전체 텍스트 반환 (불필요한 요소 제거 후)
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'button', 'input']):
            element.decompose()
        
        return soup.get_text(strip=True)
    
    @staticmethod
    def _extract_from_iframes(iframes, base_url):
        """iframe에서 텍스트 추출"""
        all_text = []
        
        for iframe in iframes:
            try:
                # iframe의 src 속성 가져오기
                src = iframe.get('src')
                if not src:
                    continue
                
                # 상대 URL을 절대 URL로 변환
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                elif not src.startswith('http'):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                
                logger.info(f"iframe src 추출 시도: {src}")
                
                # iframe 내용 가져오기
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': base_url
                }
                
                response = requests.get(src, headers=headers, timeout=10)
                response.raise_for_status()
                
                iframe_soup = BeautifulSoup(response.content, 'html.parser')
                
                # iframe 내부에서 텍스트 추출
                text = WebTextExtractor._extract_general_content(iframe_soup)
                if text and len(text.strip()) > 10:
                    all_text.append(text)
                    logger.info(f"iframe에서 텍스트 추출 성공: {len(text)}자")
                
            except Exception as e:
                logger.warning(f"iframe 텍스트 추출 실패: {e}")
                continue
        
        if all_text:
            return ' '.join(all_text)
        else:
            logger.warning("모든 iframe에서 텍스트 추출 실패")
            return None
    
    @staticmethod
    def _extract_from_iframes_selenium(driver, iframes, base_url):
        """Selenium으로 iframe에서 텍스트 추출"""
        all_text = []
        
        for i, iframe in enumerate(iframes):
            try:
                # iframe으로 전환
                driver.switch_to.frame(iframe)
                
                # iframe 내부에서 텍스트 추출
                try:
                    # 본문 요소 찾기
                    content_selectors = [
                        'main', 'article', '.main-content', '.content', 
                        '.post-content', '.entry-content', '.article-content'
                    ]
                    
                    text = ""
                    for selector in content_selectors:
                        try:
                            element = driver.find_element(By.CSS_SELECTOR, selector)
                            text = element.text
                            if text and len(text.strip()) > 10:
                                break
                        except:
                            continue
                    
                    # 본문을 찾지 못한 경우 body 전체 텍스트
                    if not text or len(text.strip()) <= 10:
                        text = driver.find_element(By.TAG_NAME, "body").text
                    
                    if text and len(text.strip()) > 10:
                        all_text.append(text)
                        logger.info(f"Selenium iframe {i+1}에서 텍스트 추출 성공: {len(text)}자")
                
                finally:
                    # 기본 컨텍스트로 돌아가기
                    driver.switch_to.default_content()
                
            except Exception as e:
                logger.warning(f"Selenium iframe {i+1} 텍스트 추출 실패: {e}")
                # 기본 컨텍스트로 돌아가기
                try:
                    driver.switch_to.default_content()
                except:
                    pass
                continue
        
        if all_text:
            return ' '.join(all_text)
        else:
            logger.warning("모든 Selenium iframe에서 텍스트 추출 실패")
            return None

class ComplianceAnalyzer:
    """의료광고법 준수 분석 클래스 - 2025년 대한의사협회 심의기준 반영"""
    
    # 2025년 최신 의료광고법 기준 위반 항목들
    COMPLIANCE_RULES = {
        '과장·절대적 표현': {
            'keywords': [
                '100% 효과', '100% 완치', '100% 치료', '완벽해결', '완전 치료', 
                '부작용 없음', '절대적', '최고', '최상', '최우수', '최고급',
                '세계최초', '세계 최초', '국내최초', '국내 최초', '국내유일', '국내 유일',
                '혁신적', '획기적', '놀라운', '기적적', '마법같은', '완벽한',
                '확실한', '보장', '약속', '반드시', '무조건', '항생제 처방률 최저',
                '국내 최상품', '대표적', '최고 수준', '세계 수준'
            ],
            'severity': 'high',
            'description': '객관적 근거 없는 과장·절대적 표현은 의료광고법 위반입니다.',
            'penalty': '1년 이하 징역 또는 1,000만원 이하 벌금, 업무정지 1~2개월',
            'legal_basis': '의료법 제27조 제3항, 의료광고 심의기준',
            'improvement_guide': '객관적 근거 자료와 함께 "개인차가 있을 수 있습니다" 등의 주의사항 명시'
        },
        
        '비교광고': {
            'keywords': [
                '다른 병원보다', '타 의료기관 대비', '경쟁사 대비', '타원 대비',
                '일반 치료보다', '기존 방법보다', '다른 곳보다', '타 병원 대비',
                '경쟁 병원', '타 의료진', '다른 의사'
            ],
            'severity': 'high',
            'description': '다른 의료기관과의 비교광고는 금지됩니다.',
            'penalty': '1년 이하 징역 또는 1,000만원 이하 벌금',
            'legal_basis': '의료법 제27조 제3항 제2호',
            'improvement_guide': '자기 의료기관의 특장점만을 객관적으로 설명하되, 타 기관과의 비교 표현 삭제'
        },

        '환자체험담·후기': {
            'keywords': [
                '환자가 말하는', '실제 후기', '치료 경험담', '환자 인터뷰',
                '생생한 후기', '치료 후기', '수술 후기', '환자 경험',
                '치료받은 환자', '실제 환자', '환자 증언', '환자 이야기',
                '후기', '리뷰', '경험담', '체험기', '추천', '만족도'
            ],
            'severity': 'high',
            'description': '환자 후기·경험담을 광고 목적으로 활용하는 것은 금지됩니다.',
            'penalty': '1년 이하 징역 또는 1,000만원 이하 벌금',
            'legal_basis': '의료법 제27조 제3항 제7호',
            'improvement_guide': '환자 후기 대신 의료진의 전문적인 치료 설명이나 의학적 정보 제공'
        },

        '신의료기술 미평가 광고': {
            'keywords': [
                '최신 해외 기술', '승인 준비중', '곧 도입 예정', '임상시험 중',
                '연구 중인', '개발 중인', '시험 적용', '파일럿 프로그램',
                '베타 테스트', '실험적 치료', '미승인 기술', '최첨단 기술'
            ],
            'severity': 'high',
            'description': '신의료기술평가를 받지 않은 시술·기술 광고는 금지됩니다.',
            'penalty': '1년 이하 징역 또는 1,000만원 이하 벌금',
            'legal_basis': '의료법 제53조, 신의료기술평가에 관한 규칙',
            'improvement_guide': '식품의약품안전처 허가 또는 신의료기술평가 완료된 기술만 광고 가능'
        },

        '환자 유인·알선': {
            'keywords': [
                '할인', '이벤트', '특가', '무료', '공짜', '증정', '사은품',
                '쿠폰', '적립', '포인트', '캐시백', '리베이트', '커미션',
                '소개비', '추천료', '중개', '알선', '유인', '모객', '무료상담',
                '무료검진', '특별가격', '론칭 이벤트', '오픈 기념'
            ],
            'severity': 'high',
            'description': '환자 유인·알선 행위는 의료법 위반입니다.',
            'penalty': '3년 이하 징역 또는 3,000만원 이하 벌금, 자격정지 2개월 이상',
            'legal_basis': '의료법 제27조 제1항, 제2항',
            'improvement_guide': '정상적인 진료비 안내와 의료 정보 제공에 집중, 금전적 혜택 표현 삭제'
        },

        '치료효과 보장': {
            'keywords': [
                '효과 보장', '결과 보장', '성공 보장', '만족 보장',
                '확실한 효과', '보장된 결과', '약물치료 없이 완치',
                '100% 성공', '실패 없는', '확실한 치료', '반드시 나아집니다'
            ],
            'severity': 'high',
            'description': '치료효과를 보장하는 표현은 금지됩니다.',
            'penalty': '1년 이하 징역 또는 1,000만원 이하 벌금',
            'legal_basis': '의료법 제27조 제3항 제6호',
            'improvement_guide': '"개인별 차이가 있을 수 있습니다", "충분한 상담 후 결정하시기 바랍니다" 등의 주의사항 필수'
        },

        '질병 공포감 조성': {
            'keywords': [
                '방치하면 위험', '생명이 위험', '돌이킬 수 없는', '치료 안 받으면',
                '큰일납니다', '심각한 결과', '위험한 상태', '응급상황',
                '치명적', '생명을 위협', '돌이킬 수 없다', '위험합니다'
            ],
            'severity': 'medium',
            'description': '질병에 대한 공포감을 조성하는 표현은 적절하지 않습니다.',
            'penalty': '업무정지 또는 과태료 300만원 이하',
            'legal_basis': '의료광고 심의기준 제8조',
            'improvement_guide': '질병의 객관적 설명과 조기 진단의 중요성을 균형 있게 설명'
        },

        '의료진 개인정보': {
            'keywords': [
                '졸업 대학', '출신 대학', '학력 사항', '개인 경력',
                '사적 정보', '개인 이력', '학교 출신', '대학 전공',
                '개인적 배경', '가족 관계', '개인 신상'
            ],
            'severity': 'medium',
            'description': '의료진의 개인정보를 과도하게 노출하는 것은 부적절합니다.',
            'penalty': '시정명령 또는 과태료 100만원 이하',
            'legal_basis': '개인정보보호법, 의료광고 심의기준',
            'improvement_guide': '의료진의 전문 자격, 진료 경력 등 의료 관련 정보만 명시'
        },

        '전후사진 부적절 사용': {
            'keywords': [
                '비포 애프터', '전후 비교', '시술 전후', '치료 전후',
                '변화 과정', '개선 사진', '결과 사진', '치료 결과'
            ],
            'severity': 'medium',
            'description': '전후사진은 명확한 의료적 근거와 설명이 함께 제공되어야 합니다.',
            'penalty': '정정광고 명령 또는 업무정지 1개월',
            'legal_basis': '의료광고 심의기준 제11조',
            'improvement_guide': '전후사진 사용 시 촬영 조건, 개인차 안내, 부작용 정보 필수 포함'
        },

        'SNS 미심의 광고': {
            'keywords': [
                '인스타그램', '페이스북', '유튜브', '틱톡', '블로그',
                '포스팅', '업로드', 'SNS', '소셜미디어', '온라인 홍보',
                '인플루언서', '광고협찬', '체험단'
            ],
            'severity': 'high',
            'description': '10만명 이상 플랫폼에서의 광고는 개별계정 이용자 수와 관계없이 사전심의가 필수입니다.',
            'penalty': '1년 이하 징역 또는 1,000만원 이하 벌금',
            'legal_basis': '보건복지부 고시 제2024-270호 (2024.11.4)',
            'improvement_guide': '대한의사협회 의료광고심의위원회 사전심의 접수 필수 (심의수수료: 1~5면 11만원)'
        },

        '의료광고 범주 벗어남': {
            'keywords': [
                '의약품 광고', '의료기기 광고', '전문의약품', '특정 의료기기',
                '약물 효능', '기기 사양', '제품 설명', '브랜드 광고'
            ],
            'severity': 'high',
            'description': '의료광고가 아닌 의약품·의료기기 광고는 별도 심의가 필요합니다.',
            'penalty': '접수 불가, 별도 심의 절차 필요',
            'legal_basis': '의료광고 심의기준 제2조',
            'improvement_guide': '의료기관 진료 서비스 중심으로 광고 내용 구성, 특정 제품 홍보 삭제'
        },

        '글자크기 부적절': {
            'keywords': [
                '작은 글씨', '미세한 글자', '읽기 어려운', '글자 크기',
                '폰트 사이즈', '가독성', '시인성'
            ],
            'severity': 'low',
            'description': '온라인 광고 시 최소 글자크기 14 이상 필수입니다.',
            'penalty': '심의 불가, 재작성 요구',
            'legal_basis': '의료광고 심의기준 제15조',
            'improvement_guide': '모든 텍스트를 14pt 이상으로 설정, 중요 정보는 더 큰 글자로 표시'
        }
    }

    # 2025년 기준 권장 표현 가이드
    RECOMMENDED_EXPRESSIONS = {
        '과장표현': {
            '100% 효과': '효과는 개인별 차이가 있을 수 있습니다',
            '완벽한 치료': '의료진과 충분한 상담 후 결정하시기 바랍니다',
            '세계최초': '관련 분야 임상 경험을 보유하고 있습니다',
            '국내유일': '해당 분야 전문의가 진료합니다',
            '부작용 없음': '부작용 및 주의사항에 대해 의료진과 상담하시기 바랍니다',
            '완전 치료': '치료 결과는 개인의 상태에 따라 달라질 수 있습니다',
            '확실한 효과': '개별 진단을 통해 적합한 치료 방법을 안내드립니다'
        },
        '후기관련': {
            '실제 환자 후기': '치료 경험은 개인마다 다를 수 있습니다',
            '환자 인터뷰': '정확한 정보는 의료진과 상담하시기 바랍니다',
            '치료 후기': '개별 상담을 통해 정확한 정보를 확인하세요',
            '만족도 조사': '의료진의 전문적인 진료 상담을 받으시기 바랍니다'
        },
        '효과보장': {
            '효과 보장': '치료 결과는 개인차가 있을 수 있습니다',
            '확실한 효과': '의료진과 상담을 통해 적합성을 확인하세요',
            '성공 보장': '치료 계획은 개별 진단에 따라 달라집니다',
            '만족 보장': '충분한 상담과 설명을 통해 진료합니다'
        },
        '유인표현': {
            '할인 이벤트': '정상적인 진료비 안내는 전화 또는 방문 상담',
            '무료 검진': '건강보험 적용 진료 항목에 대한 안내',
            '특가 제공': '의료급여 및 보험 적용 항목 확인 가능',
            '무료 상담': '진료 상담은 예약제로 운영됩니다'
        },
        '공포조성': {
            '방치하면 위험': '조기 진단의 중요성에 대해 안내드립니다',
            '큰일납니다': '정기적인 검진을 권장합니다',
            '생명이 위험': '해당 질환의 특성과 치료 방법을 설명드립니다'
        }
    }

    # 대한의사협회 심의 기준
    KMA_REVIEW_CRITERIA = {
        'pre_review_required_platforms': [
            '인스타그램', '페이스북', '유튜브', '틱톡', '네이버 블로그',
            '카카오스토리', '트위터', '링크드인'
        ],
        'review_fees': {
            '1-5면': '11만원',
            '6-10면': '22만원', 
            '11-15면': '33만원',
            '16-20면': '44만원',
            '21면 이상': '55만원'
        },
        'minimum_font_size': 14,
        'unacceptable_cases': [
            '의료광고 범주 벗어남',
            '수정사항 과도 (전체 내용의 50% 이상)',
            '의학적 객관성 부족',
            '의료법 제56조 2항 위반'
        ]
    }

    @classmethod
    def analyze_text(cls, text):
        """텍스트를 분석하여 의료광고법 준수 여부를 검사"""
        violations = []
        recommendations = []
        severity_score = 0
        
        # 위반 항목 검사
        for category, rule in cls.COMPLIANCE_RULES.items():
            found_violations = []
            for keyword in rule['keywords']:
                if keyword.lower() in text.lower():
                    found_violations.append(keyword)
            
            if found_violations:
                violations.append({
                    'category': category,
                    'description': rule['description'],
                    'severity': rule['severity'],
                    'found_keywords': found_violations,
                    'penalty': rule['penalty'],
                    'legal_basis': rule['legal_basis'],
                    'improvement_guide': rule['improvement_guide'],
                    'violation_count': len(found_violations)
                })
                
                severity_score += (20 if rule['severity'] == 'high' else 
                                 10 if rule['severity'] == 'medium' else 5) * len(found_violations)

        # 권장 표현 검사 및 개선 방안 제시
        for category, expressions in cls.RECOMMENDED_EXPRESSIONS.items():
            for original, improved in expressions.items():
                if original.lower() in text.lower():
                    recommendations.append({
                        'category': category,
                        'original_text': original,
                        'improved_text': improved,
                        'reason': f'{category} 위반 방지를 위한 2025년 기준 권장 표현으로 변경',
                        'importance': 'high' if category in ['과장표현', '효과보장', '후기관련'] else 'medium'
                    })

        # 점수 계산
        score = max(0, 100 - severity_score)
        status = '적합' if score >= 80 else '부분적합' if score >= 60 else '부적합'
        risk_level = 'high' if severity_score >= 40 else 'medium' if severity_score >= 20 else 'low'

        # 추가 검사 항목
        needs_pre_review = any(platform in text.lower() for platform in 
                              [p.lower() for p in cls.KMA_REVIEW_CRITERIA['pre_review_required_platforms']])
        needs_evidence = any(v['category'] in ['과장·절대적 표현', '치료효과 보장'] for v in violations)
        needs_disclaimer = len(violations) > 0
        
        # 심의 수수료 계산 (대략적 추정)
        estimated_pages = max(1, len(text) // 2000)  # 2000자당 1페이지로 추정
        review_fee = cls._calculate_review_fee(estimated_pages)

        return {
            'violations': violations,
            'recommendations': recommendations,
            'compliance_checklist': {
                'pre_review_required': needs_pre_review,
                'review_number_needed': needs_pre_review,
                'medical_evidence_required': needs_evidence,
                'disclaimer_needed': needs_disclaimer,
                'estimated_pages': estimated_pages,
                'estimated_review_fee': review_fee,
                'font_size_check': '최소 14pt 이상 글자크기 필수',
                'kma_contact': '대한의사협회 의료광고심의위원회 (02-794-2474)'
            },
            'improvement_summary': {
                'total_violations': len(violations),
                'high_severity_count': sum(1 for v in violations if v['severity'] == 'high'),
                'medium_severity_count': sum(1 for v in violations if v['severity'] == 'medium'),
                'low_severity_count': sum(1 for v in violations if v['severity'] == 'low'),
                'total_recommendations': len(recommendations),
                'priority_actions': cls._get_priority_actions(violations)
            },
            'overall_score': score,
            'compliance_status': status,
            'risk_level': risk_level,
            'analysis_date': timezone.now().isoformat()
        }
    
    @classmethod
    def _calculate_review_fee(cls, pages):
        """심의 수수료 계산"""
        if pages <= 5:
            return '11만원'
        elif pages <= 10:
            return '22만원'
        elif pages <= 15:
            return '33만원'
        elif pages <= 20:
            return '44만원'
        else:
            return '55만원'
    
    @classmethod
    def _get_priority_actions(cls, violations):
        """우선순위 개선 행동 항목 반환"""
        priority_actions = []
        
        high_severity = [v for v in violations if v['severity'] == 'high']
        if high_severity:
            priority_actions.append({
                'priority': 1,
                'action': '고위험 위반 사항 즉시 수정',
                'description': f"{len(high_severity)}개의 고위험 위반 사항을 우선적으로 수정해야 합니다.",
                'categories': list(set(v['category'] for v in high_severity))
            })
        
        sns_violations = [v for v in violations if 'SNS' in v['category']]
        if sns_violations:
            priority_actions.append({
                'priority': 2,
                'action': '대한의사협회 사전심의 접수',
                'description': 'SNS 플랫폼 광고 시 사전심의가 필수입니다.',
                'contact': '대한의사협회 의료광고심의위원회 (02-794-2474)'
            })
        
        if len(violations) > 5:
            priority_actions.append({
                'priority': 3,
                'action': '전체 광고 내용 재검토',
                'description': '다수의 위반 사항으로 인해 전체적인 광고 내용 재구성이 필요합니다.',
                'recommendation': '의료광고 전문가 상담 권장'
            })
        
        return priority_actions 