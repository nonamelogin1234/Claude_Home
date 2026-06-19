# ПРОЕКТЫ — СТАТУСЫ

> Обновлять после каждой рабочей сессии.
> Структура: `projects/` — код, `infra/` — конфиги/сервисы, `archive/` — заморожено.

## Код-проекты (projects/)

| Проект | Статус | Следующий шаг | Папка |
|--------|--------|---------------|-------|
| 📐 ВК Методичка (Word-документы) | 🟢 R1–R7 готовы | Проверить docx руками, при необходимости дополнить; R8 (итоговый раздел) опционально | projects/vk-metodichka/ |
| 🎬 КиноКлод | 🔴 Сервис упал | Поднять kinoclaude.service на VPS (`systemctl start kinoclaude`) | projects/kinoclaude/ |
| ⚔️ RPG Трекер | 🟢 Работает | Проверить водопад визуально на https://mcp.myserver-ai.ru:8769/ | projects/rpg-tracker/ |
| 🏗️ RuRevitMCP | 🟡 В процессе | PartUtils даёт 92.4 м³, нужно 83. Найдены 3 класса ошибок (верхняя зона, Z<0, двойной счёт). Следующий шаг: Boolean Union солидов + клипирование Z=0..2920мм | projects/revit-mcp/ |
| 📄 ИУЛ | 🟡 В процессе | Вернуться к v1 Tkinter как приоритетной версии; v2 PySide6 отменена | projects/iul/ |
| 📰 Grok-News | 🟢 Работает | Добавить виджет погоды (нужен OWM ключ) | projects/grok-news/ |
| ⏳ Таймер до отпуска | 🟢 Готово | Использовать ярлык `До отпуска` на рабочем столе до 29.05.2026 | projects/vacation-timer/ |

## Инфраструктура (infra/)

| Проект | Статус | Следующий шаг | Папка |
|--------|--------|---------------|-------|
| 🏡 Homepage + Authelia | 🟢 Работает | Сменить пароль Authelia (Admin2026! — временный) | infra/homepage/ |
| 📊 Мониторинг (Grafana) | 🟢 Работает | Вписать Telegram bot_token в alertmanager | infra/dashboard/ |
| 🕵️ VPN Hide (анти-DPI) | 🟢 Работает | Проверить Hysteria2 на мобильном интернете | infra/vpn-hide/ |
| 📱 IKEv2 VPN (Samsung) | 🟢 Работает | Сделать nftables-правила persistent (/etc/nftables.conf) | infra/strongswan/ |
| 🎵 Navidrome | 🟢 Работает | Создать admin-пользователя, залить музыку | infra/navidrome/ |
| 🏠 Домашний сервер | 🟢 Работает | Настроить мобильное приложение Immich | infra/homeserver/ |
| 🦞 OpenClaw personal secretary | 🟡 В процессе | Слой 1 базово развернут: память assistant_*, поиск по контексту, личность Когтя-робота и команда «Переходим в новый чат». Следующий шаг: улучшить UX классификации “запомни” и убрать тестовые записи при необходимости | infra/openclaw/ |
| 🏃 Health Sync | 🟢 Работает | Проверить cron для ScaleConnect | infra/health-sync/ |
| 🖥️ VM Discord-VPN | ✅ Завершено (май 2026) | — | — |
| 🖥️ MCP серверы (домашний ПК) | 🟡 В процессе | Telegram MCP работает и проверен; осталось отдельно поставить/проверить `windows-mcp` (`pip install uv` → `uvx windows-mcp`) | — |
| 🖥️ MCP серверы (рабочий ПК, Claude Desktop) | 🟢 Работает | `fetch` и `revit-mcp` починены (2026-06-17). fetch: прямой путь к exe вместо uvx. revit-mcp: правильный пакет `mcp-server-for-revit` + `cmd /c`. Осталось: postgres (DPI), telegram (сессия). | — |
| 🔒 VPN killswitch для Claude (рабочий ПК) | 🟢 Готово | Точечные правила Windows Firewall (Allow только через интерфейс `AmneziaVPN` + Block остального) для `claude.exe`/`Claude.exe`. Грабля: пути версионные, после обновления Claude нужно пересоздавать правила вручную. Чек-лист для повторения на домашнем ПК и зеркалирования универсальных memory-правил (PushNotification при `AskUserQuestion`) и недостающих MCP — в `brain/workstations.md`. См. также `brain/grabli.md` и `brain/core-work.md`. | — |
| 🖨️ Принтеры рабочего ПК с AmneziaVPN | 🟢 Готово (2026-06-19) | Kyocera TASKalfa 3253ci KX (192.168.1.100) и HP Designjet T770 (192.168.1.5) работают при включённом VPN. Фикс: Ethernet interface metric → 2, /32 persistent host routes для принтеров, ARP flush. Всё в grabli.md. | — |
| 🔑 ClaudeAdminExec (рабочий ПК) | 🟢 Готово | Scheduled task для выполнения команд от админа без UAC: `C:\Users\torganov-a\admin-exec\` (cmd_in.ps1 → schtasks /run /tn ClaudeAdminExec → cmd_out.txt). См. `brain/grabli.md` | — |
| ⚙️ 3proxy ulimit | 🟡 В процессе | systemd override: `LimitNOFILE=65536` в `/etc/systemd/system/3proxy.service.d/override.conf` | — |
| 📲 Telegram Desktop без VPN | 🟡 Частично работает | Свой MTProxy `147.45.238.120:9443` подключается с `dd`, но медиа качает нестабильно; тему пока закрыли | — |
| 🧦 Proxifier + Discord | 🚫 Закрыто | Заменено VM Discord-VPN. Proxifier Standard не поддерживает UDP, голос не работал | — |
| 🔑 SSH ключ домашнего ПК | 🔴 Нужно сделать | После переустановки Windows — сгенерировать новый ключ и добавить в VPS + домашний сервер | — |

## В архиве (archive/)

| Проект | Почему | Папка |
|--------|--------|-------|
| Codex (RPG v1) | Заменён rpg-tracker (White Lotus тема) | archive/codex/ |
| DocAI | Заморожен: RAG по PDF не в приоритете | archive/docai/ |

## Сервисы без папки в репо

| Сервис | Где | Статус | Адрес |
|--------|-----|--------|-------|
| n8n | VPS Docker :5678 | 🟢 | https://myserver-ai.ru |
| PostgreSQL (jarvis_memory) | VPS Docker | 🟢 | — |
| Vaultwarden | VPS Docker :8081 | 🟢 | https://vault.myserver-ai.ru |
| Uptime Kuma | Домашний сервер :3001 | 🟢 | http://192.168.0.106:3001 |
| qbittorrent | Домашний сервер :18080 | 🟢 | http://192.168.0.106:18080 |
| Jellyfin | Домашний сервер :8096 | 🟢 | http://192.168.0.106:8096 |
| Samba | Домашний сервер | 🟢 | \\192.168.0.106\Jellyfin (user: sergei) |
| VM Discord-VPN | Домашний ПК (VirtualBox) | 🟢 | SSH: localhost:2222, user: cthu |
