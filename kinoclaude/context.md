# 🎬 КиноКлод

## ЦЕЛЬ
Система кинорекомендаций в Claude Desktop. Клод советует фильмы на основе профиля вкусов, использует Кинопоиск как источник данных, запоминает оценки пользователя в PostgreSQL.

## СТАТУС
🟢 MCP подключён и работает. Следующий шаг — таблицы БД + инструменты для оценок.

## ЧТО СДЕЛАНО
- [2026-03-25] Написан kinoclaude_mcp.py на FastMCP 3.1.1, инструменты: search_films, get_film, get_top_films, get_films_by_filters, get_film_staff
- [2026-03-25] Systemd сервис kinoclaude.service запущен на порту 8766, проксируется nginx на 8767 (HTTPS)
- [2026-03-25] Переключён транспорт с `http` на `sse` (FastMCP http даёт 406 в Claude Desktop)
- [2026-03-25] claude_desktop_config.json: kinoclaude подключён через `npx mcp-remote@latest`
- [2026-03-25] Все 5 инструментов проверены — работают

## СЛЕДУЮЩИЙ ШАГ
Создать таблицы БД в PostgreSQL и добавить инструменты: rate_film, get_my_ratings, recommend.

## ГРАБЛИ
- FastMCP 3.1.1 в режиме `http` возвращает 406 на запросы от Claude Desktop
- Claude Desktop НЕ поддерживает `type: sse` напрямую — только stdio. Для remote SSE нужен bridge: `npx mcp-remote@latest <url>`
- claude_desktop_config.json не переносит trailing comma — писать JSON только через Python json.dump()

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
```
Файл:    /opt/kinoclaude/kinoclaude_mcp.py
Сервис:  kinoclaude.service (порт 8766, SSE транспорт)
Порт:    8766 (localhost) → nginx → 8767 (HTTPS)
SSE URL: https://mcp.myserver-ai.ru:8767/sse
API:     kinopoiskapiunofficial.tech
Токен:   33455aff-64f4-4f82-849e-e98473c46ce8 (500 req/day)
```

Таблицы БД (ещё не созданы):
- `kinoclaude_ratings` — film_id, title, my_rating, status, date
- `kinoclaude_blacklist` — фильмы «никогда не смотрю»
- `kinoclaude_profile` — JSON профиль вкусов
