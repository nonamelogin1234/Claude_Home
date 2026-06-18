# ЯДРО — ДОМАШНИЙ ПК (no-na)

> Этот файл читать, если репозиторий открыт по пути `C:\Users\no-na\Desktop\2027\Codex_Home` или пользователь Windows — `no-na`.

## 🔒 ЖЁСТКОЕ ПРАВИЛО — VPN не трогать

**НИКОГДА не отключать, не перезапускать, не менять настройки VPN-клиента (AmneziaVPN) и его killswitch на этом компьютере — ни напрямую, ни как побочный шаг диагностики/фикса чего-либо другого.**
Это касается любых команд: отключение службы, `netsh`, правка маршрутов, перезапуск процесса VPN, снятие killswitch ради "проверить интернет" и т.п. Если что-то не работает и есть подозрение на VPN — **сообщить пользователю и спросить**, самому не лезть.
Причина: настроен точечный killswitch — Claude не может выйти в сеть мимо VPN. Случайное отключение убивает всю защиту.

## Окружение

- Репо: `C:\Users\no-na\Desktop\2027\Codex_Home`
- Компьютер: домашний ПК (user: no-na)
- srv.ps1 (VPS): `C:\Users\no-na\srv.ps1`
- home.ps1 (домашний сервер): `C:\Users\no-na\home.ps1`
- timeweb-vps.ps1 (аварийное управление VPS): `C:\Users\no-na\timeweb-vps.ps1`
- Язык общения: русский, коммиты тоже по-русски

## Git — каждая сессия

```powershell
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

## MCP/инструменты на этом компьютере

См. `brain/workstations.md`, раздел "Домашний ПК" — там зафиксированы: desktop-commander, windows-mcp, git, fetch, puppeteer, memory, postgres (SSH-туннель), telegram, sequential-thinking, n8n. Конфиг: `C:\Users\no-na\.claude\settings.json`.

## Знания — как найти

**Поиск по всей базе:**
```bash
python brain/search.py "wireguard"
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

## Правила (ключевые)

- `brain/grabli.md` — только дополнять снизу, **никогда не удалять**
- Перед нетривиальным кодом (>2 файлов, новый сервис) — обсудить архитектуру
- Настроили MCP/инструмент/ключ → зафиксировать в `brain/workstations.md`
- Секреты не в коде и не в репо
- После значимой задачи — коммит
- Пути в файлах — всегда относительные от корня репо
- **Если пользователь говорит "сделали на рабочем/домашнем — сделай и здесь"** → открыть `brain/workstations.md`, найти настройку, сравнить пути текущего компьютера, применить только нужное

## Compact Instructions

При сжатии контекста сохранять: текущую задачу, статус проекта, последние грабли, факт что мы на домашнем ПК.
