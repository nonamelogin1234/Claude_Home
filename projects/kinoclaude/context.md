# 🎬 КиноКлод

## ЦЕЛЬ
Система кинорекомендаций в Claude Desktop. Клод советует фильмы на основе профиля вкусов, использует Кинопоиск как источник данных, запоминает оценки пользователя в PostgreSQL.

## СТАТУС
🟢 Полная система работает. MCP подключён, БД заполнена, профиль готов.

## ЧТО СДЕЛАНО
- [2026-03-25] Написан kinoclaude_mcp.py на FastMCP 3.1.1, инструменты: search_films, get_film, get_top_films, get_films_by_filters, get_film_staff
- [2026-03-25] Systemd сервис kinoclaude.service запущен на порту 8766, проксируется nginx на 8767 (HTTPS)
- [2026-03-25] Переключён транспорт с `http` на `sse` (FastMCP http даёт 406 в Claude Desktop)
- [2026-03-25] claude_desktop_config.json: kinoclaude подключён через `npx mcp-remote@latest`
- [2026-03-28] Таблицы PostgreSQL: kinoclaude_ratings (710 записей), kinoclaude_blacklist
- [2026-03-28] Загружена история просмотров из kinoclaude_ratings.md (UTF-16 TSV, 710 фильмов/сериалов)
- [2026-03-28] Обогащение через KP API: 415/710 записей с жанрами, тегами, рейтингами (остальные 402 — платный доступ)
- [2026-03-28] Новые MCP-инструменты: get_my_ratings, rate_film, get_profile, add_to_blacklist, get_blacklist
- [2026-03-28] Создан profile.md — профиль вкусов киномана на основе 710 просмотренных
- [2026-03-28] Создан recommend_prompt.md — инструкция для сценария «Посоветуй фильм»

## СЛЕДУЮЩИЙ ШАГ
Протестировать сценарий «Посоветуй фильм» в Claude Desktop:
1. Открыть Claude Desktop
2. Ввести «Посоветуй фильм»
3. Проверить что Claude читает профиль, задаёт вопросы, исключает просмотренное

## ГРАБЛИ
- FastMCP 3.1.1 в режиме `http` возвращает 406 на запросы от Claude Desktop
- Claude Desktop НЕ поддерживает `type: sse` напрямую — только stdio. Для remote SSE нужен bridge: `npx mcp-remote@latest <url>`
- claude_desktop_config.json не переносит trailing comma — писать JSON только через Python json.dump()
- GitHub raw кэшируется ~5-10 мин → для срочного деплоя передавать файлы через base64 + Shell API
- kinoclaude_ratings.md — формат UTF-16 LE (BOM), не UTF-8
- KP API /v2.2/films/{id} возвращает 402 для некоторых фильмов (платный доступ нужен)
- Shell API на VPS таймаутит при командах >60с → использовать nohup + фоновый запуск

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
```
Файл:    /opt/kinoclaude/kinoclaude_mcp.py
Профиль: /opt/kinoclaude/profile.md
Сервис:  kinoclaude.service (порт 8766, SSE транспорт)
Порт:    8766 (localhost) → nginx → 8767 (HTTPS)
SSE URL: https://mcp.myserver-ai.ru:8767/sse
API:     kinopoiskapiunofficial.tech
Токен:   33455aff-64f4-4f82-849e-e98473c46ce8 (500 req/day)
```

Таблицы БД:
- `kinoclaude_ratings` — film_id, kp_type, title, title_ru, year, my_rating, status, date_watched, genres[], tags[], kp_rating, imdb_rating, description, enriched_at
- `kinoclaude_blacklist` — film_id, title, reason, added_at

MCP-инструменты (всего 10):
- search_films, get_film, get_top_films, get_films_by_filters, get_film_staff (Кинопоиск API)
- get_my_ratings, rate_film, get_profile, add_to_blacklist, get_blacklist (личная БД)
