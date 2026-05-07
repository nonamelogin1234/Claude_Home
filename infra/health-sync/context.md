# HEALTH SYNC — СИНХРОНИЗАЦИЯ ДАННЫХ ЗДОРОВЬЯ

## ЦЕЛЬ
Скрипты синхронизации данных здоровья в PostgreSQL (jarvis_memory).
Три источника: весы Picooc (ScaleConnect), Health Connect (шаги/сон/пульс), Hevy (тренировки).

## СТАТУС
🟢 Все три синхронизатора работают — данные пишутся в PostgreSQL

## ИСТОЧНИКИ ДАННЫХ

| Источник | Папка на VPS | Таблица в БД | Как запускается |
|---|---|---|---|
| Весы Picooc | /opt/scaleconnect/ | body_measurements | sync.sh (cron?) |
| Health Connect | /opt/health-connect/ | health_daily_summary | sync_health.sh / n8n |
| Hevy тренировки | /opt/hevy/ | hevy_workouts, hevy_sets | sync_hevy.sh / n8n |

## ЧТО СДЕЛАНО
- ScaleConnect: клиент API Picooc → CSV → PostgreSQL (body_measurements)
- Health Connect: парсинг .zip экспорта → SQLite → PostgreSQL (health_daily_summary)
- Hevy: парсинг workout_data.csv → PostgreSQL (hevy_workouts + hevy_sets)
- n8n Workflow: Health Connect sync (ID: 01BCs4rVxAKdi01J, запуск 7:30 МСК)
- n8n Workflow: Hevy sync (ID: pWp8TqJNVngiOOVZ, запуск /6h)

## СЛЕДУЮЩИЙ ШАГ
- Убедиться что ScaleConnect cron настроен (проверить crontab -l на VPS)
- Документировать формат данных в health_daily_summary

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
```
# ScaleConnect
Папка:   /opt/scaleconnect/
Скрипт:  sync.sh → fetch_activity.py → PostgreSQL
Данные:  latest.csv, mifitness.csv
Конфиг:  config.yaml, scaleconnect.json

# Health Connect  
Папка:   /opt/health-connect/
Скрипт:  parse_health_db.py — парсит SQLite из zip-экспорта
Zip:     /opt/health-connect/Здоровье и спорт (1).zip
БД:      health_connect_export.db (промежуточная SQLite)

# Hevy
Папка:   /opt/hevy/
Скрипт:  parse_hevy_csv.py + sync_hevy.sh
CSV:     workout_data.csv (экспорт из Hevy app)

# PostgreSQL таблицы
body_measurements:     weight (float), measured_at (timestamp)
health_daily_summary:  steps, sleep, pulse, energy_kcal, date
hevy_workouts:         агрегат тренировок (дата, название, объём)
hevy_sets:             каждый подход (с 2026-03-25)
```

## ГРАБЛИ
- health_daily_summary: energy в Health Connect хранится в миллиКалориях → делить на 1000
- body_measurements: колонка weight (не value), дата measured_at (не date)
- psql не установлен на VPS хосте → проверять через docker exec postgres psql
