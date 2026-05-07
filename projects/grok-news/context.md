# GROK-NEWS — НОВОСТНАЯ СВОДКА + ЗДОРОВЬЕ

## ЦЕЛЬ
Сервис на VPS: генерирует ежедневную новостную сводку через Grok API (xAI)
и отдаёт статистику здоровья из PostgreSQL.
Используется как виджет на Homepage (home.myserver-ai.ru).

## СТАТУС
🟢 Работает — systemd grok-news.service, порт 8770

## ЧТО СДЕЛАНО
- [2026-04-15] Написан server.py — HTTP сервер на Python stdlib (без фреймворков)
- [2026-04-15] Эндпоинты: /health-stats (вес, курение, прогресс), /summary (Grok новости)
- [2026-04-15] Подключён к PostgreSQL jarvis_memory (body_measurements, health_daily_summary)
- [2026-04-15] Systemd сервис настроен, nginx проксирует /grok-news/ на home.myserver-ai.ru
- [2026-04-15] Добавлен виджет customapi в Homepage widgets.yaml

## СЛЕДУЮЩИЙ ШАГ
- Добавить виджет погоды (нужен OpenWeatherMap API ключ)
- Возможно: расширить /summary на здоровье за неделю

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
```
Файл:    /opt/grok-news/server.py
.env:    /opt/grok-news/.env  (GROK_API_KEY=...)
Сервис:  grok-news.service (systemd, enabled, running)
Порт:    8770 (только localhost, nginx проксирует)
Модель:  grok-3-latest (api.x.ai)
БД:      PostgreSQL 172.18.0.4, jarvis_memory

# Эндпоинты
GET  /health-stats  → {weight, goal, smoke_days, diff, progress_pct}
POST /summary       → {summary, timestamp}

# Nginx location (в конфиге homepage)
location /grok-news/ { proxy_pass http://localhost:8770/; }

# Проверка
curl http://localhost:8770/health-stats

# Перезапуск
systemctl restart grok-news
```

## КОНСТАНТЫ В КОДЕ
- SMOKE_FREE_SINCE = 2025-02-13
- WEIGHT_GOAL = 85.0
- WEIGHT_START = 117.0
- Топики новостей: мировая политика, Россия, экономика, технологии, спорт

## ГРАБЛИ
- Кириллица в выводе stdout через systemctl — кракозябры, это нормально
- БД доступна только по IP 172.18.0.4 (VPS не резолвит имена контейнеров вне docker-сети)
