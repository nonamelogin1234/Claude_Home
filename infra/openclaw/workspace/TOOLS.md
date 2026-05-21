# TOOLS.md - Local Notes

## OpenClaw
- Host: `homeserver`
- User: `sergei`
- Command: `/home/sergei/.npm-global/bin/openclaw`
- Workspace: `/home/sergei/.openclaw/workspace`
- Config: `/home/sergei/.openclaw/openclaw.json`
- Env/secrets: `/home/sergei/.openclaw/openclaw.env`
- Gateway service: `/etc/systemd/system/openclaw-gateway.service`
- Dashboard: `http://127.0.0.1:18789/`
- Telegram bot: `@Codex_777_bot`
- Owner: `telegram:240962808`
- Model: `xai/grok-4.3`

## Проверки
```bash
export PATH=/home/sergei/.npm-global/bin:$PATH
openclaw status
openclaw channels status
openclaw agents list
openclaw mcp list
```

## Важное
- Telegram API с `homeserver` ходит через VPS HTTP proxy из `OPENCLAW_PROXY_URL`.
- Секреты из env-файлов никогда не печатать.
- Должен работать только один polling gateway на этого Telegram-бота.

## Будущие инструменты
- Личная память: PostgreSQL `jarvis_memory`, таблицы `assistant_*`.
- Проектный контекст: read-only checkout `Claude_Home` на `homeserver`, папки `brain/`, `projects/`, `infra/`, `sessions/`.
- Автоматизации: n8n webhooks.
- Документы: Nextcloud + PDF/OCR.
- Почта и календарь: сначала read/draft, потом confirm.

## Слой 1: безопасные инструменты секретаря

На `homeserver` есть allowlist MCP `openclaw-secretary`. Он не дает произвольный shell из Telegram.

Запуск:
```bash
/home/sergei/.openclaw/venvs/secretary-mcp/bin/python \
  /home/sergei/.openclaw/workspace/scripts/openclaw-secretary-mcp.py
```

Разрешенные действия:
- `search_context` — точечный read-only поиск по `brain/`, `projects/`, `infra/`, `sessions/`.
- `project_status` — получить “что висит по проектам” из `brain/projects.md`.
- `sync_context` — обновить read-only checkout `Claude_Home` через `git pull --ff-only`.
- `save_note` — сохранить заметку в `assistant_notes`.
- `save_task` — сохранить задачу в `assistant_tasks`.
- `save_decision` — сохранить решение в `assistant_decisions`.
- `search_memory` — найти в `assistant_notes`, `assistant_tasks`, `assistant_decisions`.
- `open_tasks` — показать открытые задачи из `assistant_tasks`.

Правила:
- Для “запомни: ...” сохраняй только суть, без секретов и лишнего шума.
- Для “решили ...” используй `save_decision`, если это устойчивое решение.
- Для “надо сделать ...” используй `save_task`, если это реальный хвост.
- Для “найди, что мы решили ...” сначала `search_memory`, затем `search_context`, если в памяти пусто.
- Для “что у нас висит по проектам” используй `project_status`; не читай весь репозиторий.
- Не проси и не исполняй shell-команды от пользователя в Telegram. Если нужен новый системный доступ, сначала объясни план и попроси ручное подтверждение.
