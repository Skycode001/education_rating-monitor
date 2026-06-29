"""
Модуль для визуализации данных
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict
from src.config import config


class DataVisualizer:
    """Класс для создания визуализаций"""
    
    @staticmethod
    def create_dashboard(current_data: pd.DataFrame, 
                        analysis: Dict, 
                        dynamics: Dict, 
                        timeline: Dict) -> go.Figure:
        """Создание интерактивной панели с графиками"""
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Основные показатели',
                'Распределение по приоритетам',
                'Динамика общего числа',
                'Баллы за индивидуальные достижения'
            ),
            specs=[
                [{"type": "indicator"}, {"type": "pie"}],
                [{"type": "scatter"}, {"type": "histogram"}]
            ]
        )

        # 1. Индикаторы (основные показатели)
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=analysis['total'],
                title={"text": "Всего подавших"},
                delta={"reference": dynamics.get('previous_total', analysis['total'])},
                domain={'row': 0, 'column': 0}
            ),
            row=1, col=1
        )
        
        # 2. Круговая диаграмма (приоритеты)
        if analysis['priority_distribution']:
            priorities = list(analysis['priority_distribution'].keys())
            counts = list(analysis['priority_distribution'].values())
            
            fig.add_trace(
                go.Pie(
                    labels=priorities,
                    values=counts,
                    hole=0.4,
                    textinfo='label+percent'
                ),
                row=1, col=2
            )
        
        # 3. Динамика (линейный график с реальным временем)
        if timeline['dates']:
            x_values = timeline.get('raw_timestamps', timeline['dates'])
            
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=timeline['totals'],
                    mode='lines+markers',
                    name='Всего',
                    line=dict(color='blue', width=2),
                    marker=dict(size=8)
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=timeline['priority_1'],
                    mode='lines+markers',
                    name='Приоритет 1',
                    line=dict(color='red', width=2),
                    marker=dict(size=8)
                ),
                row=2, col=1
            )
            
            fig.update_xaxes(
                title_text="Время обновления",
                tickformat="%d.%m %H:%M",
                row=2, col=1
            )
        
        # 4. Гистограмма баллов ИД (используем настройки из .env)
        if 'id_stats' in analysis and 'Баллы за ИД' in current_data.columns:
            id_series = current_data['Баллы за ИД'].dropna()
            if not id_series.empty:
                fig.add_trace(
                    go.Histogram(
                        x=id_series,
                        xbins=dict(
                            start=config.ID_SCORE_MIN,
                            end=config.ID_SCORE_MAX,
                            size=config.ID_SCORE_STEP
                        ),
                        name='Баллы ИД',
                        marker_color='green'
                    ),
                    row=2, col=2
                )
                
                fig.update_xaxes(
                    title_text="Баллы за ИД",
                    tickmode='linear',
                    tick0=config.ID_SCORE_MIN,
                    dtick=config.ID_SCORE_STEP,
                    range=[config.ID_SCORE_MIN - 0.5, config.ID_SCORE_MAX + 0.5],
                    row=2, col=2
                )
                fig.update_yaxes(
                    title_text="Количество абитуриентов",
                    row=2, col=2
                )
        
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="Мониторинг поступающих",
            template='plotly_white'
        )
        
        return fig

    @staticmethod
    def get_card_data(analysis: Dict, dynamics: Dict) -> Dict:
        """Подготовка данных для карточек на веб-странице"""
        return {
            'total': analysis['total'],
            'priority_1': analysis['priority_1'],
            'docs_submitted': analysis.get('docs_submitted', 0),
            'without_priority': analysis.get('without_priority', 0),
            'change': dynamics.get('total_change', 0),
            'has_history': dynamics.get('has_history', False),
            'last_updated': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }