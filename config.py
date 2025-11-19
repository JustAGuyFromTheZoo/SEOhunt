#!/usr/bin/env python3
"""Configuration settings for the bot.

Author: RedStyle
"""

import os
from pathlib import Path

from dotenv import load_dotenv


env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Bot configuration settings."""
    
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TELEGRAM_TOKEN:
        raise ValueError(
            "❌ Не найден TELEGRAM_TOKEN!\n"
            "Создайте файл .env на основе .env.example "
            "и добавьте туда токен бота."
        )
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not OPENAI_API_KEY:
        raise ValueError(
            "❌ Не найден OPENAI_API_KEY!\n"
            "Добавьте ваш OpenAI API ключ в файл .env"
        )
    
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    REQUEST_TIMEOUT = 30
    MAX_QUERIES_PER_TYPE = 10
    DEFAULT_QUERIES_COUNT = 5
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
