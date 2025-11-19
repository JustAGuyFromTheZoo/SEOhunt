#!/usr/bin/env python3
"""Query generation module using OpenAI GPT.

Generates high, medium, and low frequency search queries
based on website analysis results.

Author: RedStyle
"""

import logging
from typing import Dict, List, Optional

from openai import OpenAI

from config import Config


logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generate SEO search queries using GPT models."""
    
    def __init__(self) -> None:
        """Initialize query generator with OpenAI client."""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def generate_queries(
        self,
        analysis: Dict,
        region: Optional[str] = None,
        language: str = 'русский',
        count_per_type: int = 5
    ) -> Dict:
        """Generate search queries based on website analysis.
        
        Args:
            analysis: Website analysis results
            region: Target region for localization
            language: Query language
            count_per_type: Number of queries per type
            
        Returns:
            Dictionary containing queries by frequency type
        """
        try:
            if not analysis.get('success'):
                return {
                    'theme': 'не удалось определить',
                    'region': 'не указан',
                    'high_frequency': [
                        'Невозможно сформировать — сайт недоступен '
                        'или не содержит текста'
                    ],
                    'medium_frequency': [
                        'Невозможно сформировать — сайт недоступен '
                        'или не содержит текста'
                    ],
                    'low_frequency': [
                        'Невозможно сформировать — сайт недоступен '
                        'или не содержит текста'
                    ]
                }
            
            context = self._build_context(
                analysis, region, language, count_per_type
            )
            system_prompt = self._get_system_prompt()
            
            logger.info("Requesting GPT model for query generation")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            result = self._parse_gpt_response(result_text)
            
            logger.info("Successfully generated queries")
            return result
            
        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return {
                'theme': 'ошибка генерации',
                'region': region if region else 'не указан',
                'high_frequency': ['Ошибка при генерации запросов'],
                'medium_frequency': ['Ошибка при генерации запросов'],
                'low_frequency': ['Ошибка при генерации запросов']
            }
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for GPT model."""
        return """Ты — SEO-ассистент для Telegram-бота. Твоя задача: по информации о сайте определять тематику и предлагать списки поисковых запросов трёх типов — высокочастотные (ВЧ), среднечастотные (СЧ) и низкочастотные (НЧ), по 5–10 запросов в каждой группе.

ОПРЕДЕЛЕНИЯ ЧАСТОТНОСТИ
1. Высокочастотные (ВЧ):
   - очень общие и популярные;
   - короткие (обычно 1–2 слова, иногда 3);
   - без лишних уточнений (город, модель, редкие прилагательные).
   Примеры: "кухни на заказ", "окна пвх", "ремонт квартир", "юридические услуги".

2. Среднечастотные (СЧ):
   - уточнённые запросы с добавлением 1–2 важных уточнений;
   - длина обычно 2–4 слова;
   - могут включать тип услуги, материал, формат, но ещё не совсем «длинный хвост».
   Примеры: "кухни на заказ недорого", "кухни на заказ с установкой", "ремонт квартир под ключ цена".

3. Низкочастотные (НЧ):
   - длинные, конкретные, нишевые запросы;
   - часто включают город/район, конкретный формат услуги, дополнительные характеристики;
   - длина 3–7 и больше слов.
   Примеры: "кухни на заказ недорого в екатеринбурге", "белые кухни на заказ с барной стойкой", "ремонт однокомнатной квартиры под ключ цена екатеринбург".

ТРЕБОВАНИЯ К КАЧЕСТВУ ЗАПРОСОВ
1. Все запросы должны быть:
   - грамотно написаны;
   - соответствовать тематике сайта;
   - логичны с точки зрения реального поведения пользователей.
2. Избегай:
   - слишком общих запросов типа "кухни", "окна", "мебель", "услуги" без контекста;
   - искусственных фраз, которые люди вряд ли будут реально искать;
   - явных дублей (переупорядоченных фраз с тем же смыслом).
3. Если указан регион, обязательно включи часть НЧ и СЧ запросов с упоминанием этого региона/города.

ФОРМАТ ОТВЕТА
Отвечай СТРОГО в таком формате (без лишних пояснений):

Тема сайта: <кратко сформулированная тематика сайта>
Регион: <регион/город, если удалось определить, иначе "не указан">

Высокочастотные запросы (ВЧ):
1. ...
2. ...
3. ...
4. ...
5. ...

Среднечастотные запросы (СЧ):
1. ...
2. ...
3. ...
4. ...
5. ...

Низкочастотные запросы (НЧ):
1. ...
2. ...
3. ...
4. ...
5. ...

Не добавляй никаких примечаний, пояснений или технических комментариев."""
    
    def _build_context(
        self,
        analysis: Dict,
        region: Optional[str],
        language: str,
        count: int
    ) -> str:
        """Build context for GPT based on website analysis."""
        context_parts = []
        
        context_parts.append(f"URL сайта: {analysis.get('url', 'не указан')}")
        context_parts.append(f"Язык запросов: {language}")
        context_parts.append(
            f"Количество запросов в каждой группе: {count}"
        )
        
        if region:
            context_parts.append(f"Регион продвижения: {region}")
        elif analysis.get('region'):
            context_parts.append(
                f"Регион (определён с сайта): {analysis['region']}"
            )
        
        if analysis.get('title'):
            context_parts.append(
                f"\nЗаголовок сайта: {analysis['title']}"
            )
        
        if analysis.get('description'):
            context_parts.append(
                f"Описание сайта: {analysis['description']}"
            )
        
        if analysis.get('headings', {}).get('h1'):
            h1_list = analysis['headings']['h1'][:3]
            context_parts.append(f"Заголовки H1: {', '.join(h1_list)}")
        
        if analysis.get('headings', {}).get('h2'):
            h2_list = analysis['headings']['h2'][:5]
            context_parts.append(f"Заголовки H2: {', '.join(h2_list)}")
        
        if analysis.get('services'):
            services = analysis['services'][:10]
            context_parts.append(
                f"\nУслуги/товары на сайте:\n" +
                '\n'.join([f"- {s}" for s in services])
            )
        
        if analysis.get('unique_selling_points'):
            usp = analysis['unique_selling_points'][:5]
            context_parts.append(
                f"\nУТП (уникальные торговые предложения): "
                f"{', '.join(usp)}"
            )
        
        if analysis.get('text_content'):
            text_sample = analysis['text_content'][:500]
            context_parts.append(
                f"\nФрагмент текста с сайта: {text_sample}..."
            )
        
        context_parts.append(
            "\nСформируй поисковые запросы для этого сайта."
        )
        
        return '\n'.join(context_parts)
    
    def _parse_gpt_response(self, response_text: str) -> Dict:
        """Parse GPT response into structured format."""
        try:
            lines = response_text.strip().split('\n')
            
            result = {
                'theme': 'не определено',
                'region': 'не указан',
                'high_frequency': [],
                'medium_frequency': [],
                'low_frequency': []
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                if line.startswith('Тема сайта:'):
                    result['theme'] = line.replace('Тема сайта:', '').strip()
                elif line.startswith('Регион:'):
                    result['region'] = line.replace('Регион:', '').strip()
                elif 'Высокочастотные запросы' in line or 'ВЧ' in line:
                    current_section = 'high'
                elif 'Среднечастотные запросы' in line or 'СЧ' in line:
                    current_section = 'medium'
                elif 'Низкочастотные запросы' in line or 'НЧ' in line:
                    current_section = 'low'
                elif line and line[0].isdigit() and '.' in line:
                    query = line.split('.', 1)[1].strip()
                    
                    if current_section == 'high':
                        result['high_frequency'].append(query)
                    elif current_section == 'medium':
                        result['medium_frequency'].append(query)
                    elif current_section == 'low':
                        result['low_frequency'].append(query)
            
            if not result['high_frequency']:
                result['high_frequency'] = ['Не удалось сгенерировать']
            if not result['medium_frequency']:
                result['medium_frequency'] = ['Не удалось сгенерировать']
            if not result['low_frequency']:
                result['low_frequency'] = ['Не удалось сгенерировать']
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")
            return {
                'theme': 'ошибка парсинга',
                'region': 'не указан',
                'high_frequency': ['Ошибка обработки ответа'],
                'medium_frequency': ['Ошибка обработки ответа'],
                'low_frequency': ['Ошибка обработки ответа']
            }
