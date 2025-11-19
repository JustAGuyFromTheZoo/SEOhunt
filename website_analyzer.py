#!/usr/bin/env python3
"""Website analysis module.

Extracts content from websites and identifies key information
including theme, services, and regional data.

Author: RedStyle
"""

import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class WebsiteAnalyzer:
    """Analyze websites and extract SEO-relevant information."""
    
    def __init__(self) -> None:
        """Initialize analyzer with default settings."""
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        }
    
    async def analyze_website(self, url: str) -> Dict:
        """Analyze website and extract key information.
        
        Args:
            url: Website URL to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            logger.info(f"Fetching content from: {url}")
            
            html_content = await self._fetch_html(url)
            
            if not html_content:
                return {
                    'success': False,
                    'error': 'Не удалось получить содержимое сайта'
                }
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            analysis = {
                'success': True,
                'url': url,
                'domain': urlparse(url).netloc,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'keywords': self._extract_keywords(soup),
                'headings': self._extract_headings(soup),
                'text_content': self._extract_text_content(soup),
                'region': self._detect_region(soup),
                'services': self._extract_services(soup),
                'unique_selling_points': self._extract_usp(soup)
            }
            
            logger.info(f"Successfully analyzed: {url}")
            return analysis
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching: {url}")
            return {
                'success': False,
                'error': 'Превышено время ожидания ответа от сайта'
            }
        except Exception as e:
            logger.error(f"Error analyzing website {url}: {e}")
            return {
                'success': False,
                'error': f'Ошибка при анализе сайта: {str(e)}'
            }
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=self.headers, ssl=False) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching HTML: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлекает заголовок страницы"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Альтернатива - h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлекает meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает ключевые слова из meta keywords"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords['content'].split(',')
            return [k.strip() for k in keywords if k.strip()]
        return []
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Извлекает все заголовки H1-H3"""
        headings = {
            'h1': [],
            'h2': [],
            'h3': []
        }
        
        for tag in ['h1', 'h2', 'h3']:
            tags = soup.find_all(tag)
            headings[tag] = [h.get_text().strip() for h in tags if h.get_text().strip()]
        
        return headings
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Извлекает весь текстовый контент"""
        # Удаляем скрипты и стили
        for script in soup(['script', 'style', 'noscript']):
            script.decompose()
        
        # Получаем текст
        text = soup.get_text()
        
        # Очищаем от лишних пробелов и переносов
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Ограничиваем длину для анализа
        return text[:10000]
    
    def _detect_region(self, soup: BeautifulSoup) -> Optional[str]:
        """Определяет регион/город из контента сайта"""
        text = soup.get_text().lower()
        
        # Список крупных городов России
        cities = [
            'москва', 'москве', 'московск',
            'санкт-петербург', 'петербург', 'спб', 'санкт петербург',
            'екатеринбург', 'екатеринбурге',
            'новосибирск', 'новосибирске',
            'казань', 'казани',
            'нижний новгород', 'нижнем новгороде',
            'челябинск', 'челябинске',
            'самара', 'самаре',
            'омск', 'омске',
            'ростов-на-дону', 'ростове',
            'уфа', 'уфе',
            'красноярск', 'красноярске',
            'воронеж', 'воронеже',
            'пермь', 'перми',
            'волгоград', 'волгограде',
            'краснодар', 'краснодаре',
            'саратов', 'саратове',
            'тюмень', 'тюмени'
        ]
        
        # Нормализация городов
        city_map = {
            'москва': 'Москва', 'москве': 'Москва', 'московск': 'Москва',
            'санкт-петербург': 'Санкт-Петербург', 'петербург': 'Санкт-Петербург',
            'спб': 'Санкт-Петербург', 'санкт петербург': 'Санкт-Петербург',
            'екатеринбург': 'Екатеринбург', 'екатеринбурге': 'Екатеринбург',
            'новосибирск': 'Новосибирск', 'новосибирске': 'Новосибирск',
            'казань': 'Казань', 'казани': 'Казань',
            'нижний новгород': 'Нижний Новгород', 'нижнем новгороде': 'Нижний Новгород',
            'челябинск': 'Челябинск', 'челябинске': 'Челябинск',
            'самара': 'Самара', 'самаре': 'Самара',
            'омск': 'Омск', 'омске': 'Омск',
            'ростов-на-дону': 'Ростов-на-Дону', 'ростове': 'Ростов-на-Дону',
            'уфа': 'Уфа', 'уфе': 'Уфа',
            'красноярск': 'Красноярск', 'красноярске': 'Красноярск',
            'воронеж': 'Воронеж', 'воронеже': 'Воронеж',
            'пермь': 'Пермь', 'перми': 'Пермь',
            'волгоград': 'Волгоград', 'волгограде': 'Волгоград',
            'краснодар': 'Краснодар', 'краснодаре': 'Краснодар',
            'саратов': 'Саратов', 'саратове': 'Саратов',
            'тюмень': 'Тюмень', 'тюмени': 'Тюмень'
        }
        
        for city in cities:
            if city in text:
                return city_map.get(city, city.title())
        
        return None
    
    def _extract_services(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает список услуг/товаров"""
        services = []
        
        # Ищем списки услуг
        for ul in soup.find_all(['ul', 'ol'], limit=20):
            items = ul.find_all('li')
            for item in items[:10]:  # Максимум 10 из каждого списка
                text = item.get_text().strip()
                if text and len(text) < 100:  # Только короткие элементы
                    services.append(text)
        
        return services[:30]  # Ограничиваем общее количество
    
    def _extract_usp(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает уникальные торговые предложения (УТП)"""
        usp_keywords = [
            'недорого', 'дешево', 'низкие цены', 'скидк',
            'премиум', 'элитн', 'класс люкс',
            'быстро', 'срочно', 'за 1 день', '24 часа', 'круглосуточно',
            'под ключ', 'с установкой', 'с монтажом',
            'бесплатн', 'гарантия', 'качество',
            'опыт', 'лет на рынке', 'профессионал'
        ]
        
        text = soup.get_text().lower()
        found_usp = []
        
        for keyword in usp_keywords:
            if keyword in text:
                found_usp.append(keyword)
        
        return found_usp
