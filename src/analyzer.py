"""
Модуль для анализа данных
"""

import pandas as pd
from typing import Dict
from src.config import config


class DataAnalyzer:
    """Класс для анализа данных"""
    
    @staticmethod
    def analyze_current(df: pd.DataFrame) -> Dict:
        """Анализ текущих данных"""
        
        # Подсчет документов по ключевому слову из .env
        docs_submitted = 0
        if 'Документы' in df.columns:
            keyword = config.DOCS_SUBMITTED_KEYWORD
            docs_submitted = len(df[df['Документы'].str.contains(keyword, na=False)])
        
        result = {
            'total': len(df),
            'priority_1': len(df[df['Приоритет'] == 1]) if 'Приоритет' in df.columns else 0,
            'priority_distribution': df['Приоритет'].value_counts().to_dict() if 'Приоритет' in df.columns else {},
            'docs_submitted': docs_submitted,
            'without_priority': len(df[df['Приоритет'].isna()]) if 'Приоритет' in df.columns else 0
        }
        
        # Статистика по баллам ИД
        if 'Баллы за ИД' in df.columns and not df['Баллы за ИД'].isna().all():
            result['id_stats'] = {
                'mean': df['Баллы за ИД'].mean(),
                'median': df['Баллы за ИД'].median(),
                'max': df['Баллы за ИД'].max(),
                'min': df['Баллы за ИД'].min()
            }
        
        return result
    
    @staticmethod
    def calculate_dynamics(historical: Dict) -> Dict:
        """Расчет динамики между последним и предыдущим запусками"""
        snapshots = historical.get('snapshots', [])
        
        if len(snapshots) < 2:
            return {'has_history': False}
        
        current = snapshots[-1]
        previous = snapshots[-2]
        
        dynamics = {
            'has_history': True,
            'total_change': current['count'] - previous['count'],
            'priority_1_change': current['priority_1_count'] - previous['priority_1_count'],
            'current_total': current['count'],
            'previous_total': previous['count'],
            'current_priority_1': current['priority_1_count'],
            'previous_priority_1': previous['priority_1_count'],
            'timestamp_current': current['timestamp'],
            'timestamp_previous': previous['timestamp']
        }
        
        return dynamics
    
    @staticmethod
    def get_timeline(historical: Dict) -> Dict:
        """Подготовка данных для графика динамики с реальным временем"""
        snapshots = historical.get('snapshots', [])
        
        if not snapshots:
            return {'dates': [], 'totals': [], 'priority_1': [], 'raw_timestamps': []}
        
        dates = []
        totals = []
        priority_1 = []
        raw_timestamps = []
        
        for snap in snapshots:
            # Используем timestamp из метаданных для отображения времени
            timestamp_str = snap['timestamp']
            try:
                # Парсим время из имени файла: 20260629_203954
                from datetime import datetime
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                # Форматируем для отображения: "29.06 20:39"
                date_str = dt.strftime("%d.%m %H:%M")
                dates.append(date_str)
                raw_timestamps.append(dt)
            except:
                # Если не удалось распарсить, используем как есть
                dates.append(timestamp_str[:8])
                raw_timestamps.append(None)
            
            totals.append(snap['count'])
            priority_1.append(snap['priority_1_count'])
        
        return {
            'dates': dates,
            'totals': totals,
            'priority_1': priority_1,
            'raw_timestamps': raw_timestamps
        }