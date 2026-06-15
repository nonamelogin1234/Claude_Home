# CODEX HOME — ЯДРО

> Только самое необходимое. Полные знания — в brain/*.md, читай по запросу или ищи через search.py.

## Окружение

- Репо: `C:\Users\no-na\Desktop\2027\Codex_Home`
- Компьютер: домашний ПК (user: no-na)
- Язык общения: русский, коммиты тоже по-русски

## Git — каждая сессия

```bash
git pull                              # старт
git commit -m "описание по-русски"   # после задачи
git push                              # конец
```

## Структура репо

```
projects/   — код (kinoclaude, rpg-tracker, revit-mcp, iul, grok-news)
infra/      — конфиги сервисов (homepage, openclaw, vpn-hide, dashboard, navidrome…)
brain/      — знания, читать по запросу
archive/    — заморожено
sessions/   — саммари сессий
outputs/    — артефакты и экспорты
scripts/    — утилиты (telegram-mcp, vaultwarden-cleanup…)
```

## Серверы — команды

**VPS** (`mcp.myserver-ai.ru:7723`):
```bash
curl -sk -X POST "https://mcp.myserver-ai.ru:7723" \
  -H "X-Secret: shell-api-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"КОМАНДА"}'
```
Или: `powershell -ExecutionPolicy Bypass -File C:\Users\no-na\srv.ps1 -cmd "КОМАНДА"`

**Домашний сервер** (`mcp.myserver-ai.ru:7724`):
```bash
curl -sk -X POST "https://mcp.myserver-ai.ru:7724" \
  -H "X-Secret: home-shell-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"КОМАНДА"}'
```
Или: `powershell -ExecutionPolicy Bypass -File C:\Users\no-na\home.ps1 -cmd "КОМАНДА"`

## Знания — как найти

**Поиск по всей базе** (возвращает нужный кусок без чтения всего файла):
```bash
python brain/search.py "wireguard"
python brain/search.py "n8n docker"
python brain/search.py --build      # перестроить индекс после правок brain/
```

**Читать файл целиком когда нужен полный контекст:**

| Тема | Файл |
|------|------|
| Серверы, Docker, nginx, VPS, IP, порты, WireGuard | `brain/infra.md` |
| Что не делать — грабли и уроки | `brain/grabli.md` |
| Статусы всех проектов | `brain/projects.md` |
| MCP, инструменты, SSH-ключи, настройки по компьютерам | `brain/workstations.md` |
| Правила написания кода, архитектура | `brain/coding.md` |
| Структура репо, формат context.md | `brain/rules.md` |

**Когда читать:**
- Инфра/VPS/Docker/nginx → `brain/infra.md`
- Нетривиальный код (>2 файлов) → `brain/coding.md` + `brain/grabli.md`
- Перенос настроек между компьютерами → `brain/workstations.md`
- "Что у нас есть, с чего начать?" → `brain/projects.md`
- Новая/рискованная операция → `brain/grabli.md`

## Правила (ключевые)

- `brain/grabli.md` — только дополнять снизу, **никогда не удалять**
- Перед нетривиальным кодом (>2 файлов, новый сервис) — обсудить архитектуру
- Настроили MCP/инструмент/ключ → зафиксировать в `brain/workstations.md`
- Секреты не в коде и не в репо
- После значимой задачи — коммит
- Пути в файлах — всегда относительные от корня репо

## Compact Instructions

При сжатии контекста сохранять: текущую задачу, статус проекта, последние грабли.
