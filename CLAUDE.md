# CLAUDE CODE — ТОЧКА ВХОДА

> Читается автоматически при старте каждой сессии Claude Code.

## Контекст (загружается автоматически через @import)

См. @brain/infra.md — серверы, порты, подключения.
См. @brain/grabli.md — что не делать.
См. @brain/projects.md — статусы всех проектов.
См. @brain/rules.md — структура репо и правила.
См. @brain/coding.md — правила написания кода.
См. @brain/workstations.md — MCP, инструменты, различия компьютеров.

## Структура репозитория

```
projects/   ← код-проекты (kinoclaude, rpg-tracker, revit-mcp, iul, grok-news)
infra/      ← инфраструктура (homepage, vpn-hide, dashboard, navidrome, openclaw, ...)
archive/    ← замороженные проекты
brain/      ← системные знания (всегда читать)
sessions/   ← саммари сессий
outputs/    ← артефакты и экспорты
scripts/    ← вспомогательные скрипты (telegram-mcp, vaultwarden-cleanup, ...)
```

## Доступные MCP-серверы (домашний ПК)

| MCP | Назначение |
|-----|------------|
| `desktop-commander` | Файлы, скриншоты, shell-команды на локальном ПК |
| `windows-mcp` | Windows-специфика: реестр, процессы, сервисы |
| `git` | Git-операции в репо (`C:\Users\no-na\Desktop\2027\Codex_Home`) |
| `fetch` | Получение веб-страниц и HTTP-запросы |
| `puppeteer` | Браузерная автоматизация (Chrome) |
| `memory` | Граф знаний (`brain/memory-graph.jsonl`) |
| `postgres` | PostgreSQL `jarvis_memory` на VPS через SSH-туннель |
| `telegram` | Чтение Telegram (readonly, аккаунт 240962808) |
| `sequential-thinking` | Пошаговое мышление для сложных задач |
| `n8n` | Управление n8n workflows (нужен N8N_API_KEY в settings.json) |

## Управление серверами (из Bash-tool через curl)

```bash
# VPS:
curl -sk -X POST "https://mcp.myserver-ai.ru:7723" \
  -H "X-Secret: shell-api-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"КОМАНДА"}'

# Домашний сервер:
curl -sk -X POST "https://mcp.myserver-ai.ru:7724" \
  -H "X-Secret: home-shell-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"КОМАНДА"}'
```

Альтернатива — PowerShell-обёртки: `C:\Users\no-na\srv.ps1` и `C:\Users\no-na\home.ps1`.

## Старт сессии

1. `/start` (skill) или вручную: `git pull` в `C:\Users\no-na\Desktop\2027\Codex_Home`
2. Прочти `context.md` активного проекта, если есть
3. Одна строка подтверждения: «Прочитано: brain/ + [проект]»

## Конец сессии

По команде «пуш», «конец сессии» или «новый чат» — `/finish` (skill):
1. Обнови файлы в `brain/` и папке проекта
2. `git add -A && git commit -m "описание на русском" && git push`

## Правила

- Пути всегда относительные (от корня репо)
- Грабли (`brain/grabli.md`) только дополнять, никогда не удалять
- После каждой значимой задачи — коммит
- Язык общения: русский
- Перед нетривиальным кодом (>2 файлов, новый сервис) — архитектурное обсуждение
- Если настроили MCP/инструмент — фиксировать в `brain/workstations.md`
- Секреты не в коде и не в репо

## Compact Instructions

При сжатии контекста сохранять: текущую задачу, статус проекта, последние грабли.
