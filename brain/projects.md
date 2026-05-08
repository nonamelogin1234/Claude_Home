# ПРОЕКТЫ — СТАТУСЫ

> Обновлять после каждой рабочей сессии.
> Структура: `projects/` — код, `infra/` — конфиги/сервисы, `archive/` — заморожено.

## Код-проекты (projects/)

| Проект | Статус | Следующий шаг | Папка |
|--------|--------|---------------|-------|
| 🎬 КиноКлод | 🔴 Сервис упал | Поднять kinoclaude.service на VPS (`systemctl start kinoclaude`) | projects/kinoclaude/ |
| 🔍 DocAI | 🟡 В процессе | Вставить OpenAI API ключ в настройки, тест на реальном PDF | projects/docai/ |
| ⚔️ RPG Трекер | 🟢 Работает | Проверить водопад визуально на https://mcp.myserver-ai.ru:8769/ | projects/rpg-tracker/ |
| 🏗️ RuRevitMCP | 🟡 В процессе | Разобраться 99 vs 83 м³ (стены 1535577+1535925 — исключать?), потом упаковать в MCP-команду | projects/revit-mcp/ |
| 📄 ИУЛ | 🟡 В процессе | Ручное тестирование v2 (PySide6) после рефакторинга на поток | projects/iul/ |
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

## В архиве (archive/)

| Проект | Почему | Папка |
|--------|--------|-------|
| Codex (RPG v1) | Заменён rpg-tracker (White Lotus тема) | archive/codex/ |

## Сервисы без папки в репо

| Сервис | Где | Статус |
|--------|-----|--------|
| n8n | VPS Docker :5678 | 🟢 |
| PostgreSQL (jarvis_memory) | VPS Docker | 🟢 |
| Vaultwarden | VPS Docker :8081 | 🟢 |
| Uptime Kuma | Домашний сервер :3001 | 🟢 |
