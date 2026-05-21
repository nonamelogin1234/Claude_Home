# OpenClaw Personal Secretary

## ЦЕЛЬ
Сделать OpenClaw не девопс-ботом, а личным умным секретарем в Telegram: память, заметки, разбор мыслей, поиск по личному контексту, напоминания, документы, письма и аккуратные действия через подтверждение.

Сервер `homeserver` — только место, где секретарь живет 24/7. Инфраструктурные проверки остаются вторичной функцией по запросу.

## СТАТУС
🟡 В процессе — слой 1 развернут и проверен базовыми сценариями: OpenClaw на `homeserver`, Telegram подключен, MCP `openclaw-secretary` дает безопасную память и точечный поиск, произвольный shell запрещен exec-policy.

## ЧТО СДЕЛАНО
- [2026-05-21] OpenClaw установлен на `homeserver` под пользователем `sergei`.
- [2026-05-21] Gateway запущен как systemd service и подключен к Telegram через VPS HTTP proxy.
- [2026-05-21] Подтверждено: `openclaw channels status` показывает Telegram `connected`.
- [2026-05-21] Проверено: MCP-серверы пока не настроены.
- [2026-05-21] Принята новая рамка: OpenClaw = личный секретарь, а не мониторинг серверов.
- [2026-05-21] Создана архитектура дорогого варианта и файлы личности/поведения для workspace OpenClaw.
- [2026-05-21] В workspace OpenClaw на `homeserver` развернуты `AGENTS.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `MEMORY.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`.
- [2026-05-21] Холодный тест подтвердил новую идентичность: агент отвечает как “Коготь”, личный секретарь, не серверный мониторинг.
- [2026-05-21] В PostgreSQL `jarvis_memory` созданы таблицы `assistant_notes`, `assistant_tasks`, `assistant_decisions`, `assistant_reminders`, `assistant_user_profile`.
- [2026-05-21] Добавлен MVP cost footer: `scripts/openclaw-cost-footer.py` считает рублевую стоимость из реального OpenClaw session JSONL usage.
- [2026-05-21] Добавлены скрипты слоя 1: `scripts/secretary_context_search.py`, `scripts/secretary_memory.py`, `scripts/openclaw-secretary-mcp.py`.
- [2026-05-21] MCP `openclaw-secretary` ограничивает действия allowlist: read-only поиск по `Claude_Home` и запись только в `assistant_*`.
- [2026-05-21] На `homeserver` создан checkout `/home/sergei/Claude_Home`; до push последних коммитов актуальный `infra/openclaw` и ключевые `brain/*.md` синхронизированы вручную.
- [2026-05-21] Для MCP создан venv `/home/sergei/.openclaw/venvs/secretary-mcp` с официальным Python SDK `mcp`; самописный MCP-loop заменен на `FastMCP`.
- [2026-05-21] `openclaw-secretary` подключен в OpenClaw config и виден агенту как tools `openclaw-secretary__save_note`, `search_memory`, `search_context`, `project_status` и т.д.
- [2026-05-21] `openclaw exec-policy preset deny-all` применен: произвольный `exec` из Telegram запрещен.
- [2026-05-21] Проверены сценарии: “запомни” сохраняет в `assistant_notes`, “найди про OpenClaw” использует `search_memory` + `search_context`, “что висит по проектам” использует `project_status`, “разбери мысль” отвечает в рамке личного секретаря.
- [2026-05-21] Добавлена личность Когтя как личного тактического робота-секретаря: `SOUL.md`, настройки честности/юмора/тактичности/инициативы и сухой роботный стиль.

## СЛЕДУЮЩИЙ ШАГ
Дожать слой 1 до удобного бытового UX: убрать тестовые записи из `assistant_*` при необходимости, после push перевести `/home/sergei/Claude_Home` на чистую git-синхронизацию, добавить более умную классификацию “запомни” → note/task/decision.

## ГРАБЛИ
- Telegram API с `homeserver` напрямую таймаутится: OpenClaw должен ходить через `OPENCLAW_PROXY_URL` на VPS HTTP proxy `10.8.0.1:7779`.
- Должен работать только один polling gateway на Telegram-бота `@Codex_777_bot`.
- Не превращать OpenClaw в ежедневный шумный мониторинг. Проактивность — только по делу.
- Не давать Telegram-боту произвольный shell, удаление файлов, печать секретов или широкие права без отдельного подтвержденного режима.
- Инструменты слоя 1 должны оставаться allowlist: никакого прокидывания произвольных команд из Telegram.
- Стоимость ответа не должна считаться моделью. Только внешний post-processor по реальному `usage.cost.total`; если usage нет — не выдумывать.

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
OpenClaw:
```bash
export PATH=/home/sergei/.npm-global/bin:$PATH
openclaw status
openclaw channels status
openclaw agents list
openclaw mcp list
```

Systemd:
```bash
sudo systemctl status openclaw-gateway.service
sudo systemctl restart openclaw-gateway.service
sudo journalctl -u openclaw-gateway.service -f
```

Workspace:
```text
/home/sergei/.openclaw/workspace
```

Layer 1 MCP:
```bash
/home/sergei/.openclaw/venvs/secretary-mcp/bin/python \
  /home/sergei/.openclaw/workspace/scripts/openclaw-secretary-mcp.py
```

Context checkout:
```text
/home/sergei/Claude_Home
```

Security:
```bash
openclaw exec-policy show
```

Cost footer:
```bash
USD_RUB_RATE=90 /home/sergei/.openclaw/workspace/scripts/openclaw-cost-footer.py \
  /home/sergei/.openclaw/agents/main/sessions/SESSION.jsonl
```
