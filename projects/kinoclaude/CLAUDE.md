# КиноКлод — контекст для Claude Code

> Загружается автоматически когда Claude Code работает в папке kinoclaude/

См. @context.md — цель, статус, что сделано, следующий шаг.

## Стек
- Python, FastMCP 3.1.1, SSE транспорт
- API: kinopoiskapiunofficial.tech
- БД: PostgreSQL (jarvis_memory)

## Ключевые файлы
- `/opt/kinoclaude/kinoclaude_mcp.py` — на VPS
- Сервис: kinoclaude.service (порт 8766)
- Nginx проксирует на 8767 (HTTPS)

## Важно
- FastMCP http режим даёт 406 — использовать SSE
- Claude Desktop не поддерживает type:sse напрямую — нужен `npx mcp-remote@latest`
- claude_desktop_config.json не переносит trailing comma — писать через json.dump()
