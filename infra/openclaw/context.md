# OpenClaw Personal Secretary

## ЦЕЛЬ
Сделать OpenClaw не девопс-ботом, а личным умным секретарем в Telegram: память, заметки, разбор мыслей, поиск по личному контексту, напоминания, документы, письма и аккуратные действия через подтверждение.

Сервер `homeserver` — только место, где секретарь живет 24/7. Инфраструктурные проверки остаются вторичной функцией по запросу.

## СТАТУС
🟡 В процессе — слой 0 завершен: OpenClaw перенесен на `homeserver`, Telegram подключен, личность секретаря развернута, таблицы памяти созданы, MVP cost footer работает отдельно. Следующий слой: память и контекст.

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

## СЛЕДУЮЩИЙ ШАГ
Начать слой 1: память и контекст. Подключить `Claude_Home` на `homeserver` read-only или синхронизировать через git, сделать точечный поиск по `brain/`, `projects/`, `infra/`, `sessions/`, реализовать сохранение простых заметок/задач/решений в `assistant_*`.

## ГРАБЛИ
- Telegram API с `homeserver` напрямую таймаутится: OpenClaw должен ходить через `OPENCLAW_PROXY_URL` на VPS HTTP proxy `10.8.0.1:7779`.
- Должен работать только один polling gateway на Telegram-бота `@Codex_777_bot`.
- Не превращать OpenClaw в ежедневный шумный мониторинг. Проактивность — только по делу.
- Не давать Telegram-боту произвольный shell, удаление файлов, печать секретов или широкие права без отдельного подтвержденного режима.
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

Cost footer:
```bash
USD_RUB_RATE=90 /home/sergei/.openclaw/workspace/scripts/openclaw-cost-footer.py \
  /home/sergei/.openclaw/agents/main/sessions/SESSION.jsonl
```
