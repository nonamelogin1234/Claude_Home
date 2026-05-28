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

### Локальные приложения
- 2026-05-25: установлен настольный виджет `projects/vacation-timer/` с ярлыком `До отпуска`; запускается через `launch-vacation-timer.vbs`, переустанавливается скриптом `install-shortcut.ps1`.
- 2026-05-28: починен Notion на рабочем ПК. Симптом: `Notion.exe` 7.19.0 открывался и сразу закрывался, в логах Electron `render-process-gone` / `GPU crashed`, в Windows `APPCRASH 0x80000003`. Причина: в ACL `C:\Users\gor-r\AppData\Local\Programs` и `...\Notion` был чужой AppContainer SID `S-1-15-2-2968813833-811790644-2202111208-3784096404-1081847329-2708967783-1438471679` с FullControl, из-за чего ломалась песочница Chromium/Electron. Сделан бэкап ACL в `C:\Users\gor-r\Desktop\notion-acl-backup`, затем SID удалён рекурсивно из `AppData\Local\Programs`; Notion после этого стартует нормально.

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

## Домашний ПК — доступ к VPS (2026-05-23)

- Локальные обертки восстановлены:
  - `C:\Users\no-na\srv.ps1` → VPS shell-api `https://mcp.myserver-ai.ru:7723`
  - `C:\Users\no-na\home.ps1` → homeserver shell-api через VPS `https://mcp.myserver-ai.ru:7724`
  - `C:\Users\no-na\timeweb-vps.ps1` → аварийное управление VPS через Timeweb Cloud API
- `CLAUDE.local.md` создан локально в корне репозитория и не коммитится.
- `srv.ps1/home.ps1` зависят от живого VPS/nginx/shell-api. При полной недоступности IP `147.45.238.120` они таймаутятся.
- `timeweb-vps.ps1` не хранит токен. Перед использованием нужно установить переменную только в текущей сессии PowerShell: `Set-Item Env:TIMEWEB_CLOUD_TOKEN "..."`.
- Timeweb API ключ хранится в Vaultwarden item `API-timeweb.cloud`, поле `token`.
- 2026-05-23: настроен аварийный DPAPI-резерв Timeweb token в `C:\Users\no-na\.codex-secrets\timeweb-token.dpapi`. Файл зашифрован Windows DPAPI под пользователем `no-na`; нужен, чтобы управлять VPS даже когда Vaultwarden/VPS недоступен.
- `timeweb-vps.ps1` ищет токен в порядке: `TIMEWEB_CLOUD_TOKEN` → DPAPI-файл → Vaultwarden `API-timeweb.cloud`/`token`.
- `timeweb-vps.ps1 -action status` редактирует чувствительные поля (`root_pass`, `vnc_pass`, `password`, `token`, `secret`) перед выводом.
- Timeweb API использует официальные endpoints:
  - `GET https://api.timeweb.cloud/api/v1/servers`
  - `POST https://api.timeweb.cloud/api/v1/servers/{server_id}/start`
  - `POST https://api.timeweb.cloud/api/v1/servers/{server_id}/reboot`
  - `POST https://api.timeweb.cloud/api/v1/servers/{server_id}/shutdown`
  - `POST https://api.timeweb.cloud/api/v1/servers/{server_id}/hard-shutdown`
- Для поиска нужного сервера скрипт по умолчанию ищет IP `147.45.238.120`; если API-ответ не содержит IP в ожидаемом поле, можно передать `-serverId` вручную.
- Timeweb server id VPS `Diligent Sagittarius`: `3330663`.
- 2026-05-23: после аварии питания Timeweb `ams-1` VPS был выключен. Запуск через API `POST /servers/3330663/start` вернул HTTP timeout, но команда фактически сработала и сервер поднялся.
- После запуска обнаружен конфликт: `wg-quick@wg0` на хосте VPS был `active/enabled`, хотя `wg0` должен принадлежать только контейнеру `wg-easy`. Исправлено: `wg-quick@wg0` остановлен и отключен из автозапуска, `wg1` перезапущен через systemd и стал `active`.
