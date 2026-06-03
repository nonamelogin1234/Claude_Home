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
- 2026-05-28: штатный вход Codex в Notion — только локальный MCP-адаптер `notion_home`, а не официальный глобальный `notion` search/fetch. Код: `scripts/notion_home_mcp.py`; запуск: `C:\Users\gor-r\.codex\scripts\notion-home-mcp.ps1`; конфиг Codex: `C:\Users\gor-r\.codex\config.toml`, блок `[mcp_servers.notion_home]`. Официальный hosted `[mcp_servers.notion]` удалён из конфига, чтобы не сбивать модель в новых чатах.
- 2026-05-28: `notion_home` стартует от корневой страницы `Домашняя страница`, URL `https://www.notion.so/36ea682f4234801c8396c21a0bf1b5de`, page id `36ea682f-4234-801c-8396-c21a0bf1b5de`. Использовать инструменты `fetch_home`, `list_tree`, `fetch_page`, `fetch_page_by_title`, `search_known_pages`; не начинать работу с Notion через поиск по словам. `NOTION_API_KEY` сохранён в User environment рабочего ПК для internal integration `Codex`; секрет не хранить в репо и не печатать. Интеграция расшарена на корневую страницу, проверка `fetch_home/list_tree` успешна.
- 2026-05-28: добавлен собственный n8n MCP для Codex Desktop на рабочем ПК. Конфиг: `C:\Users\gor-r\.codex\config.toml`, блок `[mcp_servers.n8n_mcp]`; запуск: `C:\Users\gor-r\.codex\scripts\n8n-mcp.ps1`; пакет: `npx -y n8n-mcp`; URL: `https://myserver-ai.ru`. `N8N_API_URL` и `N8N_API_KEY` сохранены в User environment; секрет не хранить в репо и не печатать. Быстрая проверка запуска `npx -y n8n-mcp --help` дошла до stdio-режима и завершилась штатно по закрытию stdin.
- 2026-05-28: через n8n MCP создан и включён workflow `Call Recordings → Notion summaries` (`LDvZi8x7YlVRFMmi`). Он раз в 3 минуты смотрит Nextcloud `/Call`, берёт только новые записи после `call_recordings_settings.fresh_after_utc`, фильтрует whitelist рабочих контактов, транскрибирует и конспектирует через OpenAI HTTP API. Актуальный вывод: обычные дочерние страницы в Notion `Конспекты звонков` (`36fa682f-4234-8144-8035-c5fc0ac431b3`), не database rows. Секреты Nextcloud/Notion/OpenAI хранятся только в n8n credentials.
- 2026-05-28: тест старой записи `Анастасия Гип_260528_141612.m4a` показал: Nextcloud list отдаёт URL-encoded `path`, поэтому фильтр workflow обновлён и теперь декодирует имя файла через `decodeURIComponent`. После этого файл найден, зарезервирован и скачан. Текущий блокер: `HTTP Request` к OpenAI `/v1/audio/transcriptions` передаёт binary без нормального filename/extension, OpenAI отвечает `Invalid file format`, хотя файл `.m4a`. Родной LangChain OpenAI node транскрибирует правильнее, но не даёт активировать workflow на n8n 2.7.5. Следующий шаг: вынести транскрибацию в shell/curl helper на VPS или настроить HTTP multipart так, чтобы filename заканчивался на `.m4a`.
- 2026-05-29: workflow `Call Recordings → Notion summaries` доведён до рабочего состояния. Реальная причина `Invalid file format`: запись Samsung/телефона имела контейнер `ftyp3gp4`, то есть фактически 3GP/MP4-аудио с расширением `.m4a`; OpenAI transcription не принимал её по содержимому. В n8n добавлена цепочка: скачать Nextcloud file → взять filesystem binary id без чтения аудио в память → через VPS Shell API выполнить `docker exec n8n /home/node/.n8n/bin/ffmpeg ...` → сохранить MP3 в `/home/node/.n8n-files/` → прочитать MP3 → отправить в OpenAI transcription. Статический `ffmpeg` установлен в persistent volume n8n: `/home/node/.n8n/bin/ffmpeg` и `/home/node/.n8n/bin/ffprobe` (скачан с johnvansickle static build). Для вызова Shell API создан n8n credential `VPS shell API secret` (`httpHeaderAuth`, id `J5veduct5wGzxg2y`), секрет не печатать и не переносить в код.
- 2026-05-29: продуктовая модель конспектов переделана: Notion DB `Рабочие звонки` больше не используется как пользовательский вывод. Создана страница `Конспекты звонков` (`36fa682f-4234-8144-8035-c5fc0ac431b3`), каждый звонок создаётся отдельной дочерней page с понятным заголовком, блоками `Контекст`, `Полный пересказ`, `Ключевые выводы`, `Решения и договоренности`, `Что мне сделать после разговора`, `Действия других участников`, `Открытые вопросы`, `Риски и важные нюансы`, `Черновик follow-up`, `Теги`, `Транскрипт`. Тестовый прогон создал page `https://www.notion.so/28-05-2026-14-16-36fa682f42348118a457e2f94aabb3da`, строка `call_recordings_processed` id `345` обновлена в `done`, `transcript_len=3990`. Временный webhook удалён; workflow снова запускается только расписанием раз в 3 минуты, `saveDataSuccessExecution=none`.

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

## Домашний ПК — Vivaldi (2026-06-02)

- Профиль Vivaldi: `%LOCALAPPDATA%/Vivaldi/User Data/Default/Preferences`.
- RSS-лента для Dashboard настроена через `vivaldi.rss.settings` + `vivaldi.dashboard.widgets[].feedId`.
- Рабочая зарубежная лента: `The Guardian - World News`, URL `https://www.theguardian.com/world/rss`, `refreshInterval=120`.
- Виджет Dashboard типа `feed` привязан к `feedId` этой ленты и показывает список (`feedDisplay=list`).
- Уведомления сайтов внутри Vivaldi заблокированы глобально: `profile.default_content_setting_values.notifications=2`.
- Перед ручной правкой профиля Vivaldi нужно закрыть браузер. Резервная копия текущей правки: `%LOCALAPPDATA%/Vivaldi/User Data/Default/Preferences.codex-backup-20260602-103027`.

## Домашний ПК — железо и игры (2026-06-02)

- CPU: AMD Ryzen 5 5600H, 6 ядер / 12 потоков.
- GPU: NVIDIA GeForce RTX 3060 Laptop GPU, 6 GB VRAM, driver `596.36`; также есть встроенная AMD Radeon(TM) Graphics.
- RAM: 16 GB.
- Экраны: основной для игр `2560x1080 @ 200 Hz`; встроенный/второй `1920x1080 @ 144 Hz`.
- Mafia III (GOG): установлена в `C:/Install/Mafia III/`, exe `Mafia3.exe`, профиль в `%LOCALAPPDATA%/2K Games/Mafia III/`.
- Mafia III оптимизирована под качество + стабильные 60 fps: `videoconfig.cfg` = `0 0 2560 1080 1 0 0 1`; `profile_videosettings.pf`: high для SSAO/shadows/geometry/reflections/volumetric, AA = `1`, VSync = `true`, FPS = `1`, Motion Blur = `false`, Gameplay DOF = `false`.
- Windows Graphics Preference для `C:/Install/Mafia III/Mafia3.exe`: `GpuPreference=2` (high performance / RTX).
- Compatibility flags для `Mafia3.exe`: `HIGHDPIAWARE DISABLEDXMAXIMIZEDWINDOWEDMODE`.
- Бэкапы текущей правки Mafia III: `%LOCALAPPDATA%/2K Games/Mafia III/Saves/videoconfig.cfg.codex-backup-20260602-115509` и `%LOCALAPPDATA%/2K Games/Mafia III/Data/profiles/temporaryprofile/profile_videosettings.pf.codex-backup-20260602-115509`.

## Домашний ПК — Sony WH-1000XM4 audio toggle (2026-06-03)

- Создан переключатель Bluetooth-профиля Sony WH-1000XM4: `scripts/windows-audio/sony-wh1000xm4-mic-toggle.ps1`.
- Ярлыки на рабочем столе: `C:\Users\no-na\Desktop\Sony - подключить как микрофон.lnk` и `C:\Users\no-na\Desktop\Sony - только наушники.lnk`.
- Режим `Off` отключает `WH-1000XM4 Hands-Free`, оставляет системный вывод на `Наушники (WH-1000XM4)` и системный микрофон на `Микрофон (NVIDIA Broadcast)`.
- Режим `On` включает `WH-1000XM4 Hands-Free` и назначает вход `Головной телефон (WH-1000XM4)` системным микрофоном; при использовании Bluetooth-микрофона качество звука может перейти в hands-free режим.
- Переключатель сам запрашивает права администратора, потому что `pnputil /enable-device|/disable-device` для Bluetooth hands-free профиля требует UAC.

## Домашний ПК — рабочий стол (2026-06-03)

- Рабочий стол разобран: временное, бэкапы, debug-папки, разовые фиксы, игровые/торрентные ярлыки и старые конфиги перенесены в `C:\Users\no-na\Desktop\Редко используемое`.
- На рабочем столе оставлены: `2027`, Telegram, Discord, Docker Desktop, Photoshop 2026, Sony-переключатели, `Включить обход`, `Выключить обход`, `Добавить сайт в обход`, `Монитор доступа`.
- В меню «Пуск» создана папка ярлыков `Важное` (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Важное`) с копиями важных ярлыков. Автоматическое закрепление на начальном экране Windows 11 через shell verb блокирует для большинства ярлыков (`E_ACCESSDENIED`); Discord уже был закреплён.
