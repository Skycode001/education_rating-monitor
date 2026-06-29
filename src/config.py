"""
Конфигурация приложения из .env файла
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Находим корень проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем .env файл
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Конфигурация приложения - все настройки из .env"""
    
    # ========== Flask настройки ==========
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY не установлен в .env файле!")
    
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '127.0.0.1')
    
    # ========== Парсинг ==========
    TARGET_URL = os.getenv('TARGET_URL')
    if not TARGET_URL:
        raise ValueError("TARGET_URL не установлен в .env файле!")
    
    CACHE_DIR = os.getenv('CACHE_DIR', 'data/cache')
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 15))
    MIN_REQUEST_INTERVAL = float(os.getenv('MIN_REQUEST_INTERVAL', 2.0))
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    # ========== Анализ ==========
    DOCS_SUBMITTED_KEYWORD = os.getenv('DOCS_SUBMITTED_KEYWORD', 'Подано')
    
    # ========== Обновление ==========
    CACHE_TTL_MINUTES = int(os.getenv('CACHE_TTL_MINUTES', 10))
    AUTO_REFRESH_INTERVAL = int(os.getenv('AUTO_REFRESH_INTERVAL', 600000))
    MAX_FORCE_REFRESH_PER_HOUR = int(os.getenv('MAX_FORCE_REFRESH_PER_HOUR', 3))
    
    # ========== Визуализация ==========
    ID_SCORE_MIN = int(os.getenv('ID_SCORE_MIN', 1))
    ID_SCORE_MAX = int(os.getenv('ID_SCORE_MAX', 15))
    ID_SCORE_STEP = int(os.getenv('ID_SCORE_STEP', 1))
    
    @classmethod
    def print_config(cls):
        """Вывод текущей конфигурации (без секретов)"""
        print("\n" + "="*50)
        print("📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ")
        print("="*50)
        print(f"🖥️  Режим отладки: {cls.DEBUG}")
        print(f"🌐 Хост: {cls.HOST}:{cls.PORT}")
        print(f"🔗 URL: {cls.TARGET_URL}")
        print(f"📁 Кэш: {cls.CACHE_DIR}")
        print(f"⏱️  Интервал запросов: {cls.MIN_REQUEST_INTERVAL}с")
        print(f"⏰ Время жизни кэша: {cls.CACHE_TTL_MINUTES} мин")
        print(f"🔄 Автообновление: {cls.AUTO_REFRESH_INTERVAL//1000}с")
        print(f"📄 Ключевое слово для документов: '{cls.DOCS_SUBMITTED_KEYWORD}'")
        print(f"📊 Баллы ИД: от {cls.ID_SCORE_MIN} до {cls.ID_SCORE_MAX} с шагом {cls.ID_SCORE_STEP}")
        print("="*50 + "\n")


# Создаем объект конфигурации
config = Config()

# Выводим конфигурацию
config.print_config()