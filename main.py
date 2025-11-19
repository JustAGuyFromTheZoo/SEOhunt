#!/usr/bin/env python3
"""SEO query analysis bot for Telegram.

This module implements a Telegram bot that analyzes websites and generates
search queries of different frequency types (high, medium, low) for SEO purposes.

Author: RedStyle
"""

import logging
import re
from typing import Dict, Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import Config
from website_analyzer import WebsiteAnalyzer
from query_generator import QueryGenerator


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SEOBot:
    """Main bot class for handling SEO query generation."""
    
    def __init__(self) -> None:
        """Initialize bot with analyzer and generator components."""
        self.analyzer = WebsiteAnalyzer()
        self.generator = QueryGenerator()
    
    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        welcome_message = (
            "👋 Привет! Я SEO-ассистент.\n\n"
            "📊 Я помогу определить тематику сайта и предложу списки поисковых запросов:\n"
            "• Высокочастотные (ВЧ)\n"
            "• Среднечастотные (СЧ)\n"
            "• Низкочастотные (НЧ)\n\n"
            "📝 Просто отправь мне:\n"
            "• Ссылку на сайт (обязательно)\n"
            "• Можешь добавить: регион, язык, нишу, количество запросов\n\n"
            "Пример:\n"
            "<code>https://example.com Екатеринбург, по 7 запросов</code>\n\n"
            "Команды:\n"
            "/start - показать это сообщение\n"
            "/help - помощь по использованию"
        )
        await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    async def help_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command."""
        help_text = (
            "ℹ️ <b>Как пользоваться ботом:</b>\n\n"
            "1️⃣ Отправь ссылку на сайт (обязательно начинается с http:// или https://)\n\n"
            "2️⃣ Дополнительно можешь указать:\n"
            "   • Регион: Москва, Екатеринбург, СПб, Россия\n"
            "   • Язык: русский, английский\n"
            "   • Нишу: кухни на заказ, юридические услуги\n"
            "   • Количество: по 5, по 10 запросов\n\n"
            "3️⃣ Примеры запросов:\n"
            "   • <code>https://example.com</code>\n"
            "   • <code>https://example.com Москва</code>\n"
            "   • <code>https://example.com Екатеринбург, по 10 запросов</code>\n"
            "   • <code>https://example.com юридические услуги, Россия</code>\n\n"
            "4️⃣ Получишь списки ВЧ, СЧ и НЧ запросов для SEO-продвижения\n\n"
            "💡 По умолчанию используется русский язык и по 5-10 запросов в каждой категории."
        )
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle incoming text messages with URLs."""
        user_message = update.message.text.strip()
        
        processing_msg = await update.message.reply_text(
            "⏳ Анализирую сайт и формирую запросы...\n"
            "Это может занять 10-30 секунд."
        )
        
        try:
            url = self._extract_url(user_message)
            
            if not url:
                await processing_msg.edit_text(
                    "❌ Не найдена ссылка на сайт.\n\n"
                    "Пожалуйста, отправь сообщение с URL "
                    "(например: https://example.com)\n"
                    "Используй /help для подробной информации."
                )
                return
            
            params = self._parse_user_input(user_message, url)
            
            logger.info(f"Analyzing website: {url}")
            analysis_result = await self.analyzer.analyze_website(url)
            
            if not analysis_result['success']:
                await processing_msg.edit_text(
                    f"❌ Не удалось проанализировать сайт.\n\n"
                    f"Причина: {analysis_result.get('error', 'Неизвестная ошибка')}\n\n"
                    f"Проверь, что:\n"
                    f"• URL правильный и начинается с http:// или https://\n"
                    f"• Сайт доступен и работает\n"
                    f"• Сайт не блокирует доступ ботам"
                )
                return
            
            logger.info(f"Generating queries for: {url}")
            queries_result = self.generator.generate_queries(
                analysis_result,
                region=params.get('region'),
                language=params.get('language', 'русский'),
                count_per_type=params.get('count', 5)
            )
            
            response = self._format_response(queries_result)
            await processing_msg.delete()
            await self._send_long_message(update, response)
            
            logger.info(f"Successfully processed request for: {url}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await processing_msg.edit_text(
                "❌ Произошла ошибка при обработке запроса.\n\n"
                "Попробуй позже или отправь другой URL."
            )
    
    def _extract_url(self, text: str) -> str:
        """Extract URL from message text."""
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, text)
        if match:
            return match.group(0).rstrip('.,;:)')
        return ""
    
    def _parse_user_input(self, text: str, url: str) -> Dict[str, any]:
        """Parse additional parameters from user message."""
        
        params = {}
        text_without_url = text.replace(url, '').strip()
        
        regions = [
            'москва', 'санкт-петербург', 'спб', 'екатеринбург',
            'новосибирск', 'казань', 'нижний новгород', 'челябинск',
            'самара', 'омск', 'ростов-на-дону', 'уфа', 'красноярск',
            'воронеж', 'пермь', 'волгоград', 'краснодар', 'саратов',
            'тюмень', 'россия', 'рф'
        ]
        
        text_lower = text_without_url.lower()
        for region in regions:
            if region in text_lower:
                params['region'] = region.title()
                break
        
        if 'английский' in text_lower or 'english' in text_lower:
            params['language'] = 'английский'
        elif 'русский' in text_lower or 'russian' in text_lower:
            params['language'] = 'русский'
        
        count_match = re.search(r'по\s*(\d+)', text_lower)
        if count_match:
            params['count'] = int(count_match.group(1))
        
        if text_without_url:
            params['additional_info'] = text_without_url
        
        return params
    
    def _format_response(self, queries_result: Dict) -> str:
        """Format query results for user display."""
        response = f"<b>Тема сайта:</b> {queries_result['theme']}\n"
        response += f"<b>Регион:</b> {queries_result['region']}\n\n"
        
        response += "<b>📈 Высокочастотные запросы (ВЧ):</b>\n"
        for i, query in enumerate(queries_result['high_frequency'], 1):
            response += f"{i}. {query}\n"
        response += "\n"
        
        response += "<b>📊 Среднечастотные запросы (СЧ):</b>\n"
        for i, query in enumerate(queries_result['medium_frequency'], 1):
            response += f"{i}. {query}\n"
        response += "\n"
        
        response += "<b>📉 Низкочастотные запросы (НЧ):</b>\n"
        for i, query in enumerate(queries_result['low_frequency'], 1):
            response += f"{i}. {query}\n"
        
        return response
    
    async def _send_long_message(self, update: Update, text: str) -> None:
        """Send long message, splitting if necessary."""
        max_length = 4096
        
        if len(text) <= max_length:
            await update.message.reply_text(text, parse_mode='HTML')
        else:
            parts = []
            current_part = ""
            
            for line in text.split('\n'):
                if len(current_part) + len(line) + 1 <= max_length:
                    current_part += line + '\n'
                else:
                    parts.append(current_part)
                    current_part = line + '\n'
            
            if current_part:
                parts.append(current_part)
            
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
    
    async def error_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors in the bot."""
        logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    """Initialize and run the bot."""
    bot = SEOBot()
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message)
    )
    application.add_error_handler(bot.error_handler)
    
    logger.info("Starting SEO Assistant Bot by RedStyle...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
