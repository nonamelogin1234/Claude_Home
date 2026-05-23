# Рабочие места, MCP и локальные инструменты

> Реестр нужен, чтобы переносить настройки между рабочим и домашним компьютером без повторного объяснения “что мы там ставили и зачем”.

## Как пользоваться

Если в одном окружении настроили MCP, локальный инструмент, ключ, путь, venv, сервис или интеграцию — фиксировать здесь:

- где настроено;
- зачем нужно;
- какие файлы/пути участвуют;
- как проверить;
- как повторить на другом компьютере;
- что нельзя переносить автоматически.

Фраза для Codex: **“Мы сделали X на рабочем/домашнем компьютере. Сделай то же самое здесь.”**  
Codex должен открыть этот файл, найти X, сравнить локальные пути и применить шаги без лишней байды.

## Окружения

| Окружение | Где | Назначение | Статус |
|---|---|---|---|
| Рабочий ПК | `C:\Users\torganov-a\Documents\Claude_Home` | Codex Desktop / текущая разработка | 🟢 Активен |
| Домашний ПК | `C:\Users\no-na\...` | Домашний Codex/Claude, Windows после переустановки | 🟡 Требует проверки |
| homeserver | `/home/sergei` | OpenClaw 24/7, Telegram-бот, личный секретарь | 🟢 Активен |
| VPS | `147.45.238.120` | PostgreSQL, n8n, proxy, reverse proxy | 🟢 Активен |

## Рабочий ПК

### База
- Репо: `C:\Users\torganov-a\Documents\Claude_Home`.
- Shell: PowerShell.
- SSH ключ: `C:\Users\torganov-a\.ssh\id_ed25519`, добавлен на VPS и homeserver.
- Доступ к homeserver: через `ssh -J root@147.45.238.120 sergei@10.8.0.27`.

### MCP/инструменты Codex
Фиксировать здесь только то, что реально настраивалось руками. Встроенные инструменты Codex конкретной сессии не считать переносимой настройкой.

На 2026-05-21 отдельные локальные MCP на рабочем ПК в этой сессии не настраивались. Настройка слоя 1 OpenClaw выполнялась на `homeserver`.

## Домашний ПК

### База
- После переустановки Windows часть локальных инструментов требует перепроверки.
- Старый SSH ключ `user@Useer` утерян; нужен новый ключ и добавление на VPS + homeserver.
- Из `brain/infra.md`: MCP Claude Code на домашнем ПК хранится в `C:\Users\no-na\.claude\settings.json`.
- 2026-05-21: Firefox/Mozilla для работы с DNS Geohide настроен в профиле `C:\Users\no-na\AppData\Roaming\Mozilla\Firefox\Profiles\e18yv23p.default-release\prefs.js`: выключен DoH (`network.trr.mode=5`, `doh-rollout.self-enabled=false`) и HTTP/3 (`network.http.http3.enabled=false`). Бэкап перед правкой: `prefs.js.codex-backup-20260521-193231`.
- 2026-05-23: локальный монитор доступа для обхода установлен в `C:\zapret-flowseal\current\access_monitor.ps1` + `access_monitor.cmd`; ярлык на рабочем столе `Монитор доступа.lnk`. Проверяет Codex/ChatGPT/OpenAI в реальном времени, не меняет hosts/zapret.

### MCP/инструменты
| Инструмент | Статус | Что нужно |
|---|---|---|
| `desktop-commander` | 🟡 Не проверен | Проверить после запуска домашнего Codex/Claude |
| `windows-mcp` | 🔴 Не установлен | `python -m pip install uv` → `uvx windows-mcp` → перезапустить Claude Code |

## homeserver

### OpenClaw
- OpenClaw: `/home/sergei/.npm-global/bin/openclaw`.
- Workspace: `/home/sergei/.openclaw/workspace`.
- Config: `/home/sergei/.openclaw/openclaw.json`.
- Service: `openclaw-gateway.service`.
- Telegram: `@Codex_777_bot`, owner `telegram:240962808`.

### MCP `openclaw-secretary`
Зачем: слой 1 личного секретаря — безопасная память и точечный поиск без произвольного shell из Telegram.

Где:
- MCP script: `/home/sergei/.openclaw/workspace/scripts/openclaw-secretary-mcp.py`.
- Search script: `/home/sergei/.openclaw/workspace/scripts/secretary_context_search.py`.
- Memory script: `/home/sergei/.openclaw/workspace/scripts/secretary_memory.py`.
- Python venv: `/home/sergei/.openclaw/venvs/secretary-mcp`.
- Context checkout: `/home/sergei/Claude_Home`.

Команда MCP в OpenClaw:
```bash
/home/sergei/.openclaw/venvs/secretary-mcp/bin/python \
  /home/sergei/.openclaw/workspace/scripts/openclaw-secretary-mcp.py
```

Инструменты:
- `openclaw-secretary__save_note`
- `openclaw-secretary__save_task`
- `openclaw-secretary__save_decision`
- `openclaw-secretary__search_memory`
- `openclaw-secretary__open_tasks`
- `openclaw-secretary__search_context`
- `openclaw-secretary__project_status`
- `openclaw-secretary__sync_context`

Проверка:
```bash
openclaw mcp list
openclaw mcp show openclaw-secretary
openclaw exec-policy show
openclaw agent --session-id layer1-check --message "что у нас висит по проектам?"
```

Безопасность:
- Применено `openclaw exec-policy preset deny-all`.
- Произвольный `exec` из Telegram запрещен.
- Запись разрешена только в `assistant_*`.

Особенность:
- Для записи в PostgreSQL `jarvis_memory` используется фиксированный SSH-вызов с homeserver на VPS к Docker-контейнеру `postgres`.
- На homeserver создан SSH ключ `/home/sergei/.ssh/id_ed25519`, публичный ключ добавлен в `/root/.ssh/authorized_keys` на VPS.
- Секреты не печатать.

## VPS

### PostgreSQL `jarvis_memory`
- Docker container: `postgres`.
- База: `jarvis_memory`.
- Пользователь: `jarvis`.
- Таблицы OpenClaw: `assistant_notes`, `assistant_tasks`, `assistant_decisions`, `assistant_reminders`, `assistant_user_profile`.

Проверка с homeserver через allowlist-скрипт:
```bash
cd /home/sergei/.openclaw/workspace/scripts
python3 secretary_memory.py search-memory --json '{"query":"OpenClaw","limit":5}'
```

## Правило переноса

Когда пользователь говорит: **“мы сделали это на рабочем компьютере, сделай здесь”**:

1. Открой `brain/workstations.md`.
2. Найди соответствующий инструмент/настройку.
3. Сравни пути текущего компьютера.
4. Выполни только нужные шаги.
5. Обнови этот файл, если появились отличия.
6. Не проси заново объяснять контекст, если он уже здесь записан.
