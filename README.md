# Claude_Home

Личная рабочая среда Сергея — инфраструктура, проекты, память системы.
Управляется совместно с Claude Code.

## Структура

```
Claude_Home/
│
├── brain/                     ← системные знания (Claude читает при каждом старте)
│   ├── infra.md               ← серверы, порты, способы подключения
│   ├── projects.md            ← статусы всех проектов
│   ├── grabli.md              ← что не делать и почему
│   ├── rules.md               ← структура репо + правила ведения файлов
│   ├── coding.md              ← правила написания кода
│   ├── CHAT_INIT.md           ← инструкция для claude.ai
│   ├── Learn.md               ← размышления о направлении
│   └── skills/                ← промпты специализированных ролей Claude
│
├── projects/                  ← код-проекты (активная разработка)
│   ├── kinoclaude/            ← кинорекомендации через MCP + PostgreSQL
│   ├── docai/                 ← RAG поиск по PDF (PyQt6, pdfminer, fastembed)
│   ├── rpg-tracker/           ← RPG дашборд прогресса (FastAPI + PostgreSQL)
│   ├── revit-mcp/             ← Revit автоматизация через MCP (C#)
│   └── grok-news/             ← новостная сводка + здоровье (Grok API)
│
├── infra/                     ← инфраструктура (конфиги и документация сервисов)
│   ├── homepage/              ← стартовая страница + Authelia SSO
│   ├── dashboard/             ← мониторинг (Grafana + Prometheus)
│   ├── vpn-hide/              ← анти-DPI VPN (Hysteria2 + VLESS Reality)
│   ├── strongswan/            ← IKEv2 VPN для Samsung
│   ├── navidrome/             ← персональный музыкальный стриминг
│   ├── homeserver/            ← домашний сервер (Jellyfin, Immich, Nextcloud)
│   └── health-sync/           ← синхронизация данных здоровья в PostgreSQL
│
├── archive/                   ← замороженные/заменённые проекты
│   └── codex/                 ← RPG трекер v1 (заменён rpg-tracker)
│
├── sessions/                  ← саммари важных сессий claude.ai
│
├── CLAUDE.md                  ← точка входа для Claude Code
└── CLAUDE.local.md            ← локальные настройки (не в git)
```

## Инфраструктура

| Сервер | Где | Что крутится |
|--------|-----|-------------|
| VPS myserver-ai.ru | 147.45.238.120, Нидерланды | n8n, PostgreSQL, nginx, Docker сервисы |
| Домашний сервер | Maibenben M547, СПб | Jellyfin, Immich, Nextcloud, Navidrome |

## Запуск Claude Code

```powershell
cd "C:\Users\ИМЯ\Documents\Claude_Home"
claude
```

## Первый раз на новом компе

```powershell
git clone https://github.com/nonamelogin1234/Claude_Home "C:\Users\ИМЯ\Documents\Claude_Home"
```

Создать `CLAUDE.local.md` в корне (он в .gitignore):
```markdown
# Этот компьютер
- Имя: [рабочий / домашний]
- Пользователь: [torganov-a / user]
- Путь к srv.ps1: C:\Users\ИМЯ\srv.ps1
```

## Claude Chat (claude.ai)

При инициализации: **«читай контекст»** — читает `brain/CHAT_INIT.md` и следует инструкциям.
