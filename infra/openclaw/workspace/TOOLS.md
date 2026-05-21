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
- Личная память: PostgreSQL `jarvis_memory` + markdown summaries.
- Проектный контекст: `brain/`, `projects/*/context.md`, `infra/*/context.md`, `sessions/`.
- Автоматизации: n8n webhooks.
- Документы: Nextcloud + PDF/OCR.
- Почта и календарь: сначала read/draft, потом confirm.

