#!/usr/bin/env python
"""
Точка входа в приложение.
Запускает Flask сервер с настройками из .env
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.main import app
from src.config import config
import webbrowser
import threading
import time

# Флаг для однократного открытия браузера
browser_opened = False

def open_browser():
    """Открывает браузер только один раз"""
    global browser_opened
    if browser_opened:
        return
    # Ждем, пока сервер запустится
    time.sleep(2)
    url = f"http://{config.HOST}:{config.PORT}"
    webbrowser.open(url)
    print(f"🌐 Браузер открыт: {url}")
    browser_opened = True

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 ЗАПУСК МОНИТОРИНГА ПОСТУПАЮЩИХ")
    print("="*60)
    print(f"🌐 Открыть в браузере: http://{config.HOST}:{config.PORT}")
    print(f"📁 Кэш: {config.CACHE_DIR}")
    print(f"⏰ Обновление кэша: каждые {config.CACHE_TTL_MINUTES} минут")
    print(f"🔄 Автообновление: каждые {config.AUTO_REFRESH_INTERVAL//1000} секунд")
    print("="*60)
    print("⚙️  Для изменения настроек отредактируйте файл .env")
    print("="*60 + "\n")
    
    # Запускаем браузер в отдельном потоке
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Запускаем сервер
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=False  # <-- ВЫКЛЮЧАЕМ DEBUG чтобы не было двойного запуска
    )