"""
Flask приложение для мониторинга поступающих (упрощенная версия)
"""

from flask import Flask, render_template, jsonify, request
from src.scraper import MEPHIScraper
from src.analyzer import DataAnalyzer
from src.visualizer import DataVisualizer
from src.config import config
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
import traceback

# Получаем корневую папку проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Создаем приложение Flask с указанием папок
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['DEBUG'] = False  # Выключен для production-like режима

# Отключаем защиту от CSRF для упрощения (локальная разработка)
app.config['WTF_CSRF_ENABLED'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация компонентов
scraper = MEPHIScraper()
analyzer = DataAnalyzer()
visualizer = DataVisualizer()

# Хранилище для отслеживания частоты обновлений
force_refresh_history = {}


@app.route('/')
def index():
    """Главная страница"""
    logger.info("Запрос главной страницы")
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """API endpoint для получения данных с ограничением частоты"""
    force = request.args.get('force', 'false').lower() == 'true'
    
    # Проверяем, не слишком ли часто обновляют
    if force:
        client_ip = request.remote_addr
        now = datetime.now()
        
        if client_ip not in force_refresh_history:
            force_refresh_history[client_ip] = []
        
        # Очищаем старые записи (старше 1 часа)
        hour_ago = now - timedelta(hours=1)
        force_refresh_history[client_ip] = [
            t for t in force_refresh_history[client_ip] 
            if t > hour_ago
        ]
        
        # Проверяем лимит
        if len(force_refresh_history[client_ip]) >= config.MAX_FORCE_REFRESH_PER_HOUR:
            return jsonify({
                'error': f'Превышен лимит принудительных обновлений. '
                        f'Максимум {config.MAX_FORCE_REFRESH_PER_HOUR} в час.',
                'next_available': (now + timedelta(hours=1)).isoformat()
            }), 429
        
        force_refresh_history[client_ip].append(now)
        logger.info(f"Принудительное обновление #{len(force_refresh_history[client_ip])} "
                   f"от {client_ip}")
    
    logger.info(f"Запрос данных (force={force})")
    
    try:
        # Загружаем данные
        df = scraper.fetch_data(force=force)
        
        if df is None:
            logger.error("Не удалось загрузить данные - df is None")
            return jsonify({'error': 'Не удалось загрузить данные'}), 500
        
        if df.empty:
            logger.error("Не удалось загрузить данные - df is empty")
            return jsonify({'error': 'Данные пустые'}), 500
        
        logger.info(f"Загружено {len(df)} записей")
        
        # Сохраняем в кэш, если данные свежие
        cache_age = scraper.get_cache_age()
        if cache_age is None or cache_age > timedelta(minutes=config.CACHE_TTL_MINUTES):
            scraper.save_cache(df)
            logger.info("Данные сохранены в кэш")
        
        # Анализ данных
        current_analysis = analyzer.analyze_current(df)
        historical = scraper.get_historical_data()
        dynamics = analyzer.calculate_dynamics(historical)
        timeline = analyzer.get_timeline(historical)
        
        # Создаем визуализацию
        fig = visualizer.create_dashboard(df, current_analysis, dynamics, timeline)
        
        # Подготавливаем ответ
        response = {
            'graph': fig.to_json(),
            'cards': visualizer.get_card_data(current_analysis, dynamics),
            'dynamics': dynamics,
            'last_update': datetime.now().isoformat(),
            'cached': cache_age is not None and cache_age < timedelta(minutes=config.CACHE_TTL_MINUTES),
            'cache_ttl_minutes': config.CACHE_TTL_MINUTES,
            'force_refresh_limit': config.MAX_FORCE_REFRESH_PER_HOUR
        }
        
        logger.info(f"✅ Данные отправлены: {len(df)} записей")
        return jsonify(response)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"❌ Ошибка: {error_msg}")
        logger.error(f"❌ Трейс: {error_trace}")
        return jsonify({'error': error_msg}), 500


@app.route('/api/config')
def get_config():
    """Получение конфигурации"""
    return jsonify({
        'cache_ttl_minutes': config.CACHE_TTL_MINUTES,
        'auto_refresh_interval': config.AUTO_REFRESH_INTERVAL,
        'debug': config.DEBUG,
        'max_force_refresh_per_hour': config.MAX_FORCE_REFRESH_PER_HOUR
    })