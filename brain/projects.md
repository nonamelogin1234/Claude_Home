# ПРОЕКТЫ — СТАТУСЫ

> Обновлять после каждой рабочей сессии.
> Структура: `projects/` — код, `infra/` — конфиги/сервисы, `archive/` — заморожено.

## Код-проекты (projects/)

| Проект | Статус | Следующий шаг | Папка |
|--------|--------|---------------|-------|
| 🎬 КиноКлод | 🔴 Сервис упал | Поднять kinoclaude.service на VPS (`systemctl start kinoclaude`) | projects/kinoclaude/ |
| ⚔️ RPG Трекер | 🟢 Работает | Проверить водопад визуально на https://mcp.myserver-ai.ru:8769/ | projects/rpg-tracker/ |
| 🏗️ RuRevitMCP | 🟡 В процессе | PartUtils даёт 92.4 м³, нужно 83. Найдены 3 класса ошибок (верхняя зона, Z<0, двойной счёт). Следующий шаг: Boolean Union солидов + клипирование Z=0..2920мм | projects/revit-mcp/ |
| 📄 ИУЛ | 🟡 В процессе | Вернуться к v1 Tkinter как приоритетной версии; v2 PySide6 отменена | projects/iul/ |
| 📰 Grok-News | 🟢 Работает | Добавить виджет погоды (нужен OWM ключ) | projects/grok-news/ |

## Инфраструктура (infra/)

| Проект | Статус | Следующий шаг | Папка |
|--------|--------|---------------|-------|
| 🏡 Homepage + Authelia | 🟢 Работает | Сменить пароль Authelia (Admin2026! — временный) | infra/homepage/ |
| 📊 Мониторинг (Grafana) | 🟢 Работает | Вписать Telegram bot_token в alertmanager | infra/dashboard/ |
| 🕵️ VPN Hide (анти-DPI) | 🟢 Работает | Проверить Hysteria2 на мобильном интернете | infra/vpn-hide/ |
| 📱 IKEv2 VPN (Samsung) | 🟢 Работает | Сделать nftables-правила persistent (/etc/nftables.conf) | infra/strongswan/ |
| 🎵 Navidrome | 🟢 Работает | Создать admin-пользователя, залить музыку | infra/navidrome/ |
| 🏠 Домашний сервер | 🟢 Работает | Настроить мобильное приложение Immich | infra/homeserver/ |
| 🏃 Health Sync | 🟢 Работает | Проверить cron для ScaleConnect | infra/health-sync/ |
| 🖥️ VM Discord-VPN | ✅ Завершено (май 2026) | — | — |
| 🖥️ MCP серверы (домашний ПК) | 🟡 В процессе | `pip install uv` → `uvx windows-mcp` → перезапустить Claude Code | — |
| ⚙️ 3proxy ulimit | 🟡 В процессе | systemd override: `LimitNOFILE=65536` в `/etc/systemd/system/3proxy.service.d/override.conf` | — |
| 📲 Telegram Desktop без VPN | 🟢 Работает, ждёт проверки в клиенте | Подключить MTProto proxy в Telegram Desktop: `147.45.238.120:9443` | — |
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
