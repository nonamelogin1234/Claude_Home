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

## Чек-лист: универсальные правила Claude (auto-memory)

> Это НЕ про грабли/статусы проекта (они в `grabli.md`/`projects.md`/`context.md`). Это про правила поведения Claude, которые нужны **в каждом чате, в любом проекте, независимо от темы** — они живут в auto-memory (`~/.claude/.../memory/`), которая привязана к конкретной установке приложения на конкретной машине и НЕ синхронизируется через git.
>
> Правило: если добавил такое универсальное правило в memory на одном компьютере — добавь и на другом (текст можно адаптировать под доступные там инструменты), и отметь здесь.

| Правило | Рабочий ПК (torganov-a) | Домашний ПК (no-na) |
|---|---|---|
| При `AskUserQuestion` (или любой паузе, ждущей решения пользователя) — параллельно слать `PushNotification`, чтобы пользователь не пропустил, что процесс встал | ✅ добавлено 2026-06-16 (`feedback_notify_on_ask.md`) | ✅ добавлено 2026-06-18 (`feedback_notify_on_ask.md`) |
| ЖЁСТКОЕ правило: никогда не отключать/не трогать VPN и его killswitch, ни напрямую, ни как побочный шаг диагностики — на любом компьютере, в любом чате | ✅ добавлено 2026-06-16 (`feedback_vpn_untouchable.md`); дублируется текстуально в `brain/core-work.md` | ✅ добавлено 2026-06-18 (`feedback_vpn_untouchable.md`); продублировано в `brain/core-home.md` |

## Чек-лист: MCP-серверы Claude Desktop (2026-06-16)

> Это про `claude_desktop_config.json` (`C:\Users\<профиль>\AppData\Roaming\Claude\claude_desktop_config.json`) — он **локальный per-машина файл, НЕ в git**. Не путать с репо-шным `.mcp.json` в корне репозитория — тот синкается через `git pull` автоматически, его сюда вписывать не нужно.
>
> На рабочем ПК на 2026-06-16 в `claude_desktop_config.json` настроены:

| MCP-сервер | Пакет/команда | Секреты | Рабочий ПК | Домашний ПК |
|---|---|---|---|---|
| desktop-commander | `npx @wonderwhy-er/desktop-commander@latest` | нет | ✅ | ⬜ проверить |
| fetch | `uvx mcp-server-fetch` | нет | ✅ | ⬜ проверить |
| puppeteer | `npx @modelcontextprotocol/server-puppeteer` | нет | ✅ | ⬜ проверить |
| memory | `npx @modelcontextprotocol/server-memory` | нет (путь к `brain/memory-graph.jsonl` — поправить под локальный путь репо) | ✅ | ⬜ проверить, путь должен указывать на локальный репо домашнего ПК |
| sequential-thinking | `npx @modelcontextprotocol/server-sequential-thinking` | нет | ✅ | ⬜ проверить |
| n8n-mcp | `npx n8n-mcp` | `N8N_API_KEY` (Vaultwarden, не копировать сюда в открытом виде) | ✅ | ⬜ проверить — если нужен n8n с домашнего, взять ключ из Vaultwarden |
| shell | `npx mcp-shell` | нет | ✅ | ⬜ проверить, нужен ли вообще на домашнем |
| revit-mcp | `npx mcp-servers-for-revit` | нет | ✅ | ⬜ скорее всего НЕ нужен — Revit специфичен для рабочего ПК, ставить только если появится задача с Revit дома |
| github | `npx @modelcontextprotocol/server-github` | `GITHUB_PERSONAL_ACCESS_TOKEN` (Vaultwarden) | ✅ | ⬜ проверить, взять токен из Vaultwarden, не хардкодить новый |
| postgres | локальный скрипт `.claude/scripts/postgres-mcp.bat` из репо | нет (но путь в Desktop-конфиге абсолютный — на домашнем будет другой путь к репо) | ✅ | ⬜ проверить, путь к `.bat` поправить под локальный путь репо |
| telegram | локальный скрипт `scripts/telegram-mcp/mcp-telegram.cmd` из репо | `MCP_TELEGRAM_READONLY=1`, сессия Telegram отдельно (см. `workstations.md` выше — на 2026-06 не авторизован даже на рабочем) | 🟡 настроен, не авторизован | ⬜ проверить |

**Как доставить недостающее на домашнем ПК:** открыть `C:\Users\no-na\AppData\Roaming\Claude\claude_desktop_config.json` (создать, если файла нет), добавить нужные блоки в `mcpServers` по образцу выше, секреты взять из Vaultwarden (не вставлять в этот репо-файл), пути поправить под `C:\Users\no-na\Desktop\2027\Codex_Home`. После — перезапустить Claude Desktop и сверить список коннекторов.

## Чек-лист: VPN killswitch для Claude (точечный, по exe) — 2026-06-16

> Подробности решения и грабля про версионные пути — в `grabli.md`, раздел "Точечный killswitch для Claude (2026-06-16)". Здесь — статус по машинам.

| Шаг | Рабочий ПК (torganov-a) | Домашний ПК (no-na) |
|---|---|---|
| VPN-клиент с собственным killswitch (AmneziaVPN) | ✅ установлен, адаптер `AmneziaVPN` | ⬜ проверить, какой VPN-клиент стоит и как называется его адаптер (`Get-NetAdapter`) |
| Точечные правила Windows Firewall: Block на не-VPN адаптерах для `claude.exe` (не глобальный killswitch — другие приложения ходят напрямую) | ✅ настроено, см. `grabli.md` | ✅ настроено 2026-06-18: скрипты в `scripts/claude-killswitch/`, правила `Claude-KS-*` активны. AmneziaVPN IP: `10.8.1.2`. Ярлыки на рабочем столе: `Claude - включить killswitch.lnk`, `Claude - выключить killswitch.lnk` |
| ГЛАВНОЕ ПРАВИЛО: никогда не отключать/не трогать VPN как побочный шаг диагностики | ✅ зафиксировано в `brain/core-work.md` + в auto-memory (`feedback_vpn_untouchable.md`) | ✅ зафиксировано в `brain/core-home.md` + в auto-memory (`feedback_vpn_untouchable.md`) |
| Аварийные ярлыки на рабочем столе для ручного выключения/включения killswitch (на случай, если Claude не открывается) | ✅ `Claude-killswitch-OFF.lnk` / `Claude-killswitch-ON.lnk` + `.ico`-файлы лежат на **`C:\Users\gor-r\Desktop`** (НЕ `C:\Users\torganov-a\Desktop` — реальный рабочий стол этого Windows-сеанса на профиле `gor-r`, путь подтверждён пользователем). Иконки скачаны с iconarchive.com (Windows 8 Metro Power icons). Сами скрипты — в `C:\Users\torganov-a\admin-exec\killswitch\` (`disable.ps1`/`enable.ps1`), путь к скриптам можно оставлять под `torganov-a`, переносить на Desktop нужно только сам `.lnk`+`.ico`. Ярлыки запускают `powershell.exe -File <script>`, бит "Run as administrator" патчится напрямую в байтах `.lnk` (offset 0x15, `-bor 0x20`) — UAC всплывает при клике. После пересохранения `.lnk` через WScript.Shell (например при смене IconLocation) бит admin нужно перепроверить/перепатчить — COM-объект его не знает и может сбросить | ⬜ повторить по аналогии: уточнить актуальный путь Desktop на домашнем ПК (может тоже отличаться от ожидаемого профиля), те же 2 скрипта (DisplayName правил поменять под локальные), иконки переиспользовать или скачать свои |

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

### MCP/инструменты Claude Code (обновлено 2026-06-16)

После переустановки Claude Code на рабочем ПК `~/.claude.json`/`settings.json` оказались пустыми (ничего из проектного контекста не пострадало, потерялась только локальная MCP-конфигурация уровня приложения). Восстановлено через project-scoped `.mcp.json` в корне репо (коммитится в git, переносится автоматически при клонировании):

| Сервер | Статус | Примечание |
|---|---|---|
| `desktop-commander` | 🟢 | `npx @wonderwhy-er/desktop-commander@latest` |
| `fetch` | 🟢 | `uvx mcp-server-fetch` |
| `puppeteer` | 🟢 | `npx @modelcontextprotocol/server-puppeteer` |
| `memory` | 🟢 | `npx @modelcontextprotocol/server-memory`, файл `brain/memory-graph.jsonl` |
| `sequential-thinking` | 🟢 | `npx @modelcontextprotocol/server-sequential-thinking` |
| `n8n` | 🟢 | `npx n8n-mcp`, `N8N_API_KEY` уже лежит в User environment (не трогать/не печатать) |
| `postgres` | 🟡 Настроен, но не проверен | `.claude/scripts/postgres-mcp.bat` — SSH-туннель на VPS `172.18.0.4:5432` через ключ `id_ed25519`. **Порт 22 на VPS отвечает на TCP-connect, но SSH banner exchange таймаутится** — похоже на DPI-блокировку SSH на рабочей сети. Нужно поднимать через VPN (см. трей-индикатор VPN IP, коммит `63c5c28`), не пробовали ещё. |
| `telegram` | 🟢 Работает, полный доступ (read/write) | `node scripts/telegram-mcp/node_modules/@overpod/mcp-telegram/dist/index.js` — пакет поставлен **локально** в репо (`npm install --no-save` в `scripts/telegram-mcp/`), запуск без `npx` (старый кастомный wrapper `scripts/telegram-mcp/mcp-telegram.cmd` удалён — он искал несуществующий npm-пакет `mcp-telegram`). Авторизован 2026-06-16: публичный `api_id=2040` блокировал и QR-логин, и пересылку кода (`SEND_CODE_UNAVAILABLE`) — обошли через установку Telegram Desktop + конвертацию `tdata` → Telethon StringSession (`opentele`, без `tgcrypto`-компилятора — патч на чистом Python с `pycryptodome`, см. `brain/grabli.md`) → base64 urlsafe→standard → `~/.mcp-telegram/session`. Аккаунт: `240962808 / JesusMaan` (тот же, что на домашнем ПК). **Фикс 1**: на этом ПК Node вообще не может создавать Unix-сокеты (`net.Server.listen(path)` → `EACCES` в любой папке — системное ограничение окружения). `@overpod/mcp-telegram` поднимает IPC-сокет (`daemon.sock`) для шаринга между MCP-клиентами — без патча падал фатально. Патч в `dist/master.js` (`startOwner`): ошибка `srv.listen()` больше не реджектит promise, просто логирует и работает в режиме одного процесса. **Патч применён к локальной копии в `scripts/telegram-mcp/node_modules/...` (в `.gitignore`, не коммитится — после `npm install` в этой папке патчить заново**, искать `srv.listen(sock, resolve); srv.once("error", reject);`). **Фикс 2 (главный, 2026-06-16)**: на этом компьютере используется **Claude Desktop** (`%APPDATA%\Claude\claude_desktop_config.json`), а не CLI Claude Code — он **не читает** `.mcp.json` из репозитория, у него отдельный конфиг. Все правки `.mcp.json` были бесполезны, пока не нашли и не исправили telegram-секцию прямо в `claude_desktop_config.json`. **Если снова "ошибка загрузки" у MCP-сервера — сначала проверять `claude_desktop_config.json`, а не `.mcp.json`.** |

`notion_home`/`n8n_mcp` через `.codex/config.toml` (см. ниже) — это отдельная, более старая настройка для Codex Desktop, не для Claude Code; не путать.

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

### MCP/инструменты (домашний ПК, обновлено 2026-06-28)

**ВАЖНО**: Приложение установлено из Windows Store (MSIX), файловая система виртуализована. MCP-серверы нужно прописывать в:
`C:\Users\no-na\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
(раздел `mcpServers` на верхнем уровне). `settings.json` и `.mcp.json` этим приложением НЕ читаются.

| Инструмент | Статус | Примечание |
|---|---|---|
| `desktop-commander` | 🟢 Настроен | `npx @wonderwhy-er/desktop-commander@latest` |
| `windows-mcp` | 🟢 Настроен | `uvx windows-mcp`; uvx 0.11.14 установлен ✅ |
| `git` | 🟢 Настроен | Путь: `C:\Users\no-na\Desktop\2027\Codex_Home` (был сломан — починено 2026-06-15) |
| `fetch` | 🟢 Настроен | `uvx mcp-server-fetch` |
| `puppeteer` | 🟢 Настроен | `npx @modelcontextprotocol/server-puppeteer` |
| `memory` | 🟢 Настроен | `brain/memory-graph.jsonl` (путь был сломан — починено 2026-06-15) |
| `postgres` | 🟢 Настроен | SSH туннель через `C:\Users\no-na\.claude\scripts\postgres-mcp.bat`, ключ `id_ed25519_vps` ✅ |
| `telegram` | 🟢 Работает | `scripts/telegram-mcp/mcp-telegram-wrapper.mjs`, `MCP_TELEGRAM_READONLY=1` |
| `sequential-thinking` | 🟢 Добавлен | `npx @modelcontextprotocol/server-sequential-thinking` — для сложных задач |
| `n8n` | 🟢 Настроен | `npx n8n-mcp`, URL `https://myserver-ai.ru`; API ключ из Vaultwarden `vault.myserver-ai.ru / n8n API` (JWT) |

### Telegram MCP
- 2026-06-12: Telegram MCP на домашнем ПК доведён до рабочего состояния. `my.telegram.org/apps` не выдал новый app, поэтому использованы публичные credentials Telegram Desktop и импорт сессии из `Telegram Desktop\tdata`.
- Session store: `C:\Users\no-na\.telegram-agent`. Wrapper перед запуском делает `chdir(%USERPROFILE%)`, поэтому `TELEGRAM_AGENT_HOME=.telegram-agent` резолвится стабильно для GramJS на Windows.
- Аккаунт импортирован и проверен: `240962808 / JesusMaan`. Телефон и session string не хранить в репозитории и не печатать без необходимости.
- Проверка через MCP SDK прошла: сервер отдаёт 43 tools, `list_accounts` видит аккаунт, `list_dialogs` читает реальные диалоги.

### Telegram Feed
- 2026-06-13: пользователь отменил идею личной ИИ-ленты Telegram. До отмены был создан канал `Моя лента` (`id=4435668970`) и было подключено 50 каналов; после отмены Codex automation `telegram-feed-hourly-digest` удалена, все 50 каналов отписаны через GramJS, `joined=0`, `leave_failed=0`.
- Runtime-аудит отмены остался вне репозитория: `C:\Users\no-na\.telegram-feed\state.json`. Проектные файлы `projects/telegram-feed/` удалены до коммита.

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

## Домашний ПК — Vaultwarden cleanup (2026-06-09)

- Для массовой уборки Vaultwarden используется Bitwarden CLI `bw` (`Bitwarden.CLI` из WinGet), сервер `https://vault.myserver-ai.ru`.
- Скрипты лежат в `scripts/vaultwarden-cleanup/`:
  - `unlock-bw-session.ps1` открывать в отдельном PowerShell; пользователь вводит master password сам, скрипт сохраняет временный `BW_SESSION` в `%USERPROFILE%\.codex-secrets\bw-session.dpapi` через Windows DPAPI.
  - `cleanup-vaultwarden.ps1` делает аудит и безопасные правки: переименовывает импортированные `--` по домену URI, переносит точные дубли в `00-review-duplicates`, записи с логином/паролем без сайта в `00-review-no-site`, пустышки в `00-review-trash`.
  - `archive-review-items.ps1` делает soft-delete записей из review-папок, чтобы они исчезли из обычного списка, но оставались восстановимыми через Trash. Permanent delete включать только явным `-Permanent`.
  - `audit-password-rotation.ps1` анализирует активные записи на короткие/явно слабые/повторяющиеся пароли. Пароли не пишет в отчёт; в `outputs/vaultwarden-cleanup/` попадают только сервис, домен, маскированный логин, категория и причина.
- Перед массовыми правками сделан серверный бэкап Vaultwarden: `/opt/backups/vaultwarden/vaultwarden-20260609-104210-before-cleanup.tar.gz`.
- Отчёты лежат в `outputs/vaultwarden-cleanup/` и добавлены в `.gitignore`; не коммитить, потому что там есть имена записей/домены/маскированные логины.
- После уборки 2026-06-09: 359 записей, финальный аудит `audit-20260609-115049` показал `actionCount=0`. Временный `bw-session.dpapi` удалён, `bw lock` выполнен.
- После требования убрать мусор из общего списка 2026-06-09: soft-deleted 24 review-записи (`00-review-trash`: 1, `00-review-duplicates`: 12, `00-review-no-site`: 11). Контрольный аудит `audit-20260609-120446`: 335 обычных записей, `actionCount=0`, review-папки пустые.
- Аудит паролей 2026-06-09: `password-rotation-audit-20260609-121142` нашёл 299 кандидатов на замену из 335 активных записей; временный доступ после аудита закрыт (`bw lock`, `bw-session.dpapi` удалён).

## Домашний ПК — GTA V Enhanced mods (2026-06-14)

- GTA V Enhanced установлена в `C:\Download\Grand.Theft.Auto.V.Enhanced-InsaneRamZes\`, основной exe `PlayGTAV.exe`, игра фактически `GTA5_Enhanced.exe` версии `1.0.1013.34`.
- Моддинг-папка Codex: `C:\Download\Grand.Theft.Auto.V.Enhanced-InsaneRamZes\_codex_modding\`.
- Поставлена рабочая single-player modding-база: ScriptHookV `3788.0/1013.34`, официальный Enhanced ASI loader `xinput1_4.dll`, `dinput8.dll`, `args.txt` с `-nobattleye -noBE`, NativeTrainer, Menyoo 2.0, Add-On Vehicle Spawner, ScriptHookVDotNet Enhanced, All MP Vehicles in SP, RageOpenV, HeapAdjuster Enhanced, Packfile Limit Adjuster Enhanced, Modkit Limit Adjuster Enhanced.
- Для уверенной работы модов BattlEye exe отключен обратимо: `GTA5_Enhanced_BE.exe` переименован в `GTA5_Enhanced_BE.exe.codex-disabled`; вернуть можно обратным переименованием.
- Windows `Zone.Identifier` снят со всей папки игры, чтобы DLL/ASI не блокировались.
- Графический профиль без RT применен в `%USERPROFILE%\Documents\Rockstar Games\GTAV Enhanced\settings.xml`: RT/RTAO выключены, refresh `200`, VSync `0`, motion blur `0`. Профили лежат в `_codex_modding\settings-profile-stable-no-rt.xml` и `_codex_modding\settings-profile-rt-lite-experiment.xml`.
- Пользователь подтвердил, что моды работают. Проверочные клавиши: `F4` NativeTrainer, `F8` Menyoo, `F5` Add-On Vehicle Spawner, чит `addonspawner`.
- Следующая задача для нового чата: предложить список модов для дальнейшей установки согласно запросам пользователя. Приоритеты пользователя: родной/качественный контент в story mode из GTA Online и DLC, нормальные машины с корректными повреждениями/handling, оружие, прически, одежда, звуки и мелкие immersive-детали; графика и визуал только после контента, желательно без тяжелого RT из-за RTX 3060 Laptop 6 GB VRAM.
