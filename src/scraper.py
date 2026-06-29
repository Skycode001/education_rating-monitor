"""
Модуль для парсинга данных с сайта с рейтингом поступающих
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import os
from typing import Optional, Dict, List
from src.config import config


class MEPHIScraper:
    """Класс для загрузки и парсинга данных"""
    
    def __init__(self):
        self.url = config.TARGET_URL
        self.cache_dir = config.CACHE_DIR
        self.min_interval = config.MIN_REQUEST_INTERVAL
        self.timeout = config.REQUEST_TIMEOUT
        
        # Используем User-Agent из .env
        self.headers = {
            'User-Agent': config.USER_AGENT
        }
        self.last_request_time = None
        self.request_count = 0
        
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _respect_rate_limit(self):
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                print(f"⏳ Ожидание {wait_time:.1f}с...")
                time.sleep(wait_time)
        self.last_request_time = time.time()
        self.request_count += 1
    
    def fetch_data(self, force: bool = False) -> Optional[pd.DataFrame]:
        """Загрузка данных с сайта"""
        if not force:
            cache_age = self.get_cache_age()
            if cache_age is not None and cache_age < timedelta(minutes=config.CACHE_TTL_MINUTES):
                print(f"📂 Используем кэш (возраст: {cache_age.seconds // 60} мин)")
                return self.get_latest_cache()
        
        print(f"🔄 Загрузка свежих данных с {self.url}")
        self._respect_rate_limit()
        
        try:
            response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            
            if not table:
                print("❌ Таблица не найдена")
                return self._fallback_to_cache()
            
            rows = table.find_all('tr')
            if len(rows) < 3:
                print("❌ Слишком мало строк в таблице")
                return self._fallback_to_cache()
            
            # Находим заголовки
            header_row = None
            header_index = 0
            
            for i, tr in enumerate(rows):
                cells = tr.find_all(['th', 'td'])
                texts = [cell.get_text(strip=True) for cell in cells]
                if any('№ дела' in text for text in texts):
                    cleaned_headers = []
                    for text in texts:
                        if text.strip():
                            cleaned_headers.append(text.strip())
                        else:
                            cleaned_headers.append('')
                    
                    while cleaned_headers and not cleaned_headers[-1]:
                        cleaned_headers.pop()
                    
                    header_row = cleaned_headers
                    header_index = i
                    print(f"✅ Найдены заголовки: {header_row}")
                    break
            
            if not header_row:
                print("❌ Заголовки не найдены")
                return self._fallback_to_cache()
            
            # Собираем данные
            data_rows = []
            
            for tr in rows[header_index + 1:]:
                cells = tr.find_all(['td'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                
                if not row_data or not any(row_data):
                    continue
                
                if 'Без экзаменов' in row_data or 'Общий конкурс' in row_data:
                    continue
                
                is_valid = False
                for cell in row_data:
                    if 'НИЯУ МИФИ-' in str(cell):
                        is_valid = True
                        break
                
                if not is_valid:
                    if len(row_data) >= 2 and any(cell for cell in row_data[:2]):
                        pass
                    else:
                        continue
                
                if len(row_data) > len(header_row):
                    row_data = row_data[:len(header_row)]
                elif len(row_data) < len(header_row):
                    row_data.extend([''] * (len(header_row) - len(row_data)))
                
                row_data = [' ' if x in ['--', '-', '—', ''] else x for x in row_data]
                
                if any(x.strip() for x in row_data if x):
                    data_rows.append(row_data)
            
            if not data_rows:
                print("❌ Нет данных в таблице")
                print("🔄 Пробуем альтернативный подход...")
                for tr in rows[3:]:
                    cells = tr.find_all(['td'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    
                    if not row_data or not any(row_data):
                        continue
                    
                    if len(row_data) > len(header_row):
                        row_data = row_data[:len(header_row)]
                    elif len(row_data) < len(header_row):
                        row_data.extend([''] * (len(header_row) - len(row_data)))
                    
                    row_data = [' ' if x in ['--', '-', '—', ''] else x for x in row_data]
                    
                    if any(x.strip() for x in row_data if x):
                        data_rows.append(row_data)
            
            if not data_rows:
                print("❌ Нет данных в таблице")
                return self._fallback_to_cache()
            
            print(f"✅ Найдено {len(data_rows)} записей")
            
            df = pd.DataFrame(data_rows, columns=header_row[:len(data_rows[0])])
            
            if '№ дела' in df.columns:
                df = df[df['№ дела'].str.contains('МИФИ', na=False) | (df['№ дела'] != '')]
                df = df[df['№ дела'] != '']
            
            if 'Приоритет' in df.columns:
                df['Приоритет'] = pd.to_numeric(df['Приоритет'], errors='coerce')
            
            if 'Баллы за ИД' in df.columns:
                df['Баллы за ИД'] = pd.to_numeric(df['Баллы за ИД'], errors='coerce')
            
            if 'Сумма баллов' in df.columns:
                df['Сумма баллов'] = pd.to_numeric(df['Сумма баллов'], errors='coerce')
            
            print(f"✅ Загружено {len(df)} записей после очистки")
            
            if len(df) == 0:
                print("⚠️ После очистки не осталось записей")
                return self._fallback_to_cache()
            
            return df
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_to_cache()
    
    def _fallback_to_cache(self):
        cached = self.get_latest_cache()
        if cached is not None:
            print("📂 Возвращаем кэшированные данные")
            return cached
        return None
    
    def save_cache(self, df: pd.DataFrame) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_file = os.path.join(self.cache_dir, f"data_{timestamp}.csv")
        df.to_csv(cache_file, index=False, encoding='utf-8-sig')
        
        meta_file = os.path.join(self.cache_dir, "metadata.json")
        try:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
        except:
            metadata = {'snapshots': []}
        
        priority_1_count = 0
        if 'Приоритет' in df.columns:
            priority_1_count = len(df[df['Приоритет'] == 1])
        
        metadata['snapshots'].append({
            'timestamp': timestamp,
            'file': f"data_{timestamp}.csv",
            'count': len(df),
            'priority_1_count': priority_1_count
        })
        
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Данные сохранены в кэш: {cache_file}")
    
    def get_latest_cache(self) -> Optional[pd.DataFrame]:
        cache_files = [f for f in os.listdir(self.cache_dir) 
                      if f.startswith('data_') and f.endswith('.csv')]
        if not cache_files:
            return None
        
        latest_file = sorted(cache_files)[-1]
        df = pd.read_csv(os.path.join(self.cache_dir, latest_file))
        print(f"📂 Загружены кэшированные данные: {latest_file}")
        return df
    
    def get_cache_files(self) -> List[str]:
        return [f for f in os.listdir(self.cache_dir) 
                if f.startswith('data_') and f.endswith('.csv')]
    
    def get_cache_age(self) -> Optional[timedelta]:
        cache_files = self.get_cache_files()
        if not cache_files:
            return None
        
        latest_file = sorted(cache_files)[-1]
        timestamp_str = latest_file.replace('data_', '').replace('.csv', '')
        try:
            cache_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            return datetime.now() - cache_time
        except:
            return None
    
    def get_historical_data(self) -> Dict:
        meta_file = os.path.join(self.cache_dir, "metadata.json")
        try:
            with open(meta_file, 'r') as f:
                return json.load(f)
        except:
            return {'snapshots': []}
    
    def clear_cache(self) -> None:
        for file in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("🗑️ Кэш очищен")