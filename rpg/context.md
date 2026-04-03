# RPG ТРЕКЕР ПРОГРЕССА

## ЦЕЛЬ
Живой дашборд в стиле DnD / тёмное фэнтези — показывает прогресс тренировок, веса, сна как RPG-путешествие.

## СТАТУС
🟢 Готово — работает на VPS

## URL
**https://mcp.myserver-ai.ru:8769/**

## ЧТО СДЕЛАНО
- [2026-04-03] Написан полный код (backend + frontend + Docker) → задеплоен на VPS
- [2026-04-03] FastAPI читает PostgreSQL, DnD UI работает с живыми данными

## СЛЕДУЮЩИЙ ШАГ
Просто пользоваться!

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Backend: FastAPI, порт 8768 (внутри Docker)
- Docker: network_mode host, postgres по IP 172.18.0.4
- Nginx: /etc/nginx/sites-enabled/rpg-tracker, listen 8769 ssl, cert mcp.myserver-ai.ru
- Деплой: /opt/rpg-tracker/, исходники в rpg/
- Перезапуск: `cd /opt/rpg-tracker && docker compose restart`

## ГРАБЛИ
- Postgres доступен только по IP 172.18.0.4 (VPS не резолвит имена контейнеров вне сети)
