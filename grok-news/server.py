#!/usr/bin/env python3
"""
grok-news — новостная сводка через Grok API + health stats из PostgreSQL
Порт: 8770
"""

import os
import json
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError

GROK_API_KEY = os.environ.get('GROK_API_KEY', '')
GROK_API_URL = 'https://api.x.ai/v1/chat/completions'
GROK_MODEL = 'grok-3-latest'

DB_HOST = os.environ.get('DB_HOST', '172.18.0.4')
DB_PORT = int(os.environ.get('DB_PORT', 5432))
DB_NAME = os.environ.get('DB_NAME', 'jarvis_memory')
DB_USER = os.environ.get('DB_USER', 'jarvis')
DB_PASS = os.environ.get('DB_PASS', 'jarvis_pass')

SMOKE_FREE_SINCE = datetime.date(2025, 2, 13)
WEIGHT_GOAL = 85.0
WEIGHT_START = 117.0

PROMPT = (
    "Дай короткую яркую сводку (5-7 пунктов) самого важного за последние 24 часа по темам:\n"
    "1. Мировая политика и геополитика\n"
    "2. Мировые лидеры (решения, заявления, скандалы)\n"
    "3. ИИ и технологии\n\n"
    "Формат: по 2-3 пункта на тему. Каждый пункт — 1 предложение. "
    "Стиль: умный, прямой, без воды.\nОтвечай на русском."
)


def get_grok_summary():
    payload = json.dumps({
        'model': GROK_MODEL,
        'messages': [{'role': 'user', 'content': PROMPT}],
        'max_tokens': 1024,
        'temperature': 0.7
    }).encode('utf-8')

    req = Request(
        GROK_API_URL,
        data=payload,
        headers={
            'Authorization': f'Bearer {GROK_API_KEY}',
            'Content-Type': 'application/json'
        }
    )
    with urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content']


WEATHER_URL = (
    'https://api.open-meteo.com/v1/forecast'
    '?latitude=59.9386&longitude=30.3141'
    '&current_weather=true'
    '&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum'
    '&hourly=relativehumidity_2m,apparent_temperature,windspeed_10m'
    '&timezone=Europe%2FMoscow&forecast_days=3'
)

WMO_CODES = {
    0: 'Ясно', 1: 'Преимущественно ясно', 2: 'Переменная облачность', 3: 'Пасмурно',
    45: 'Туман', 48: 'Туман с инеем',
    51: 'Лёгкая морось', 53: 'Морось', 55: 'Густая морось',
    61: 'Небольшой дождь', 63: 'Дождь', 65: 'Сильный дождь',
    71: 'Небольшой снег', 73: 'Снег', 75: 'Сильный снег',
    77: 'Снежные зёрна',
    80: 'Ливень', 81: 'Ливни', 82: 'Сильные ливни',
    85: 'Снегопад', 86: 'Сильный снегопад',
    95: 'Гроза', 96: 'Гроза с градом', 99: 'Гроза с сильным градом',
}


def get_weather():
    try:
        with urlopen(WEATHER_URL, timeout=10) as resp:
            d = json.loads(resp.read().decode('utf-8'))

        cw = d['current_weather']
        daily = d['daily']
        hourly = d['hourly']

        # Текущий час для humidity/apparent_temp
        now_hour = datetime.datetime.now().hour
        h_idx = min(now_hour, len(hourly['relativehumidity_2m']) - 1)

        forecast = []
        day_names = ['Сегодня', 'Завтра', 'Послезавтра']
        for i in range(min(3, len(daily['time']))):
            forecast.append({
                'day': day_names[i],
                'date': daily['time'][i],
                'max': round(daily['temperature_2m_max'][i], 1),
                'min': round(daily['temperature_2m_min'][i], 1),
                'condition': WMO_CODES.get(daily['weathercode'][i], 'Неизвестно'),
                'precipitation': round(daily['precipitation_sum'][i], 1),
            })

        return {
            'temp': round(cw['temperature'], 1),
            'wind': round(cw['windspeed'], 1),
            'condition': WMO_CODES.get(int(cw['weathercode']), 'Неизвестно'),
            'humidity': hourly['relativehumidity_2m'][h_idx],
            'feels_like': round(hourly['apparent_temperature'][h_idx], 1),
            'forecast': forecast,
            'city': 'Санкт-Петербург',
            'updated': datetime.datetime.now().strftime('%H:%M'),
        }
    except Exception as e:
        return {'error': str(e)}


def get_health_stats():
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER, password=DB_PASS,
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT weight FROM body_measurements ORDER BY measured_at DESC LIMIT 1")
        row = cur.fetchone()
        weight = float(row[0]) if row else None
        cur.close()
        conn.close()
    except Exception as e:
        weight = None
        db_error = str(e)
    else:
        db_error = None

    today = datetime.date.today()
    smoke_days = (today - SMOKE_FREE_SINCE).days

    result = {
        'weight': weight,
        'goal': WEIGHT_GOAL,
        'start_weight': WEIGHT_START,
        'smoke_days': smoke_days,
        'smoke_free_since': str(SMOKE_FREE_SINCE),
        'date': str(today)
    }
    if weight is not None:
        result['diff'] = round(weight - WEIGHT_GOAL, 1)
        # progress: from start (117) to goal (85), how far gone
        total = WEIGHT_START - WEIGHT_GOAL
        gone = WEIGHT_START - weight
        result['progress_pct'] = min(100, max(0, round(gone / total * 100, 1)))
    if db_error:
        result['db_error'] = db_error
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    def _send(self, body_bytes, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body_bytes)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self._send(body, 'application/json; charset=utf-8', status)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/health':
            self.send_json({'status': 'ok', 'service': 'grok-news'})
        elif path == '/health-stats':
            self.send_json(get_health_stats())
        elif path == '/weather':
            self.send_json(get_weather())
        else:
            self.send_json({'error': 'not found'}, 404)

    def do_POST(self):
        path = self.path.split('?')[0]
        if path == '/summary':
            if not GROK_API_KEY:
                self.send_json({'error': 'GROK_API_KEY not set'}, 500)
                return
            try:
                summary = get_grok_summary()
                self.send_json({
                    'summary': summary,
                    'timestamp': datetime.datetime.now().isoformat()
                })
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_json({'error': 'not found'}, 404)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8770))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'grok-news running on :{port}', flush=True)
    server.serve_forever()
