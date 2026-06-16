# ЯДРО — РАБОЧИЙ ПК (torganov-a)

> Этот файл читать, если репозиторий открыт по пути `C:\Users\torganov-a\Documents\Claude_Home` или пользователь Windows — `torganov-a`.

## 🔒 ЖЁСТКОЕ ПРАВИЛО — VPN не трогать

**НИКОГДА не отключать, не перезапускать, не менять настройки VPN-клиента (AmneziaVPN) и его Kill Switch на этом компьютере — ни напрямую, ни как побочный шаг диагностики/фикса чего-либо другого.**
Это касается любых команд: отключение службы, `netsh`, правка маршрутов, перезапуск процесса VPN, снятие Kill Switch ради "проверить интернет" и т.п. Если что-то не работает и есть подозрение на VPN — **сообщить пользователю и спросить**, самому не лезть.
Причина: пользователь настраивает железный killswitch именно для того, чтобы Claude (и любые его процессы) физически не могли получить доступ в сеть мимо VPN. Случайное отключение VPN убивает весь смысл защиты.

## Окружение

- Репо: `C:\Users\torganov-a\Documents\Claude_Home`
- Компьютер: рабочий ПК (user: torganov-a)
- srv.ps1 (VPS): `C:\Users\torganov-a\srv.ps1`
- home.ps1 (домашний сервер): уточнить наличие — если нет, использовать curl-вариант ниже
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
Или: `powershell -ExecutionPolicy Bypass -File C:\Users\torganov-a\srv.ps1 -cmd "КОМАНДА"`

**Домашний сервер** (`mcp.myserver-ai.ru:7724`):
```bash
curl -sk -X POST "https://mcp.myserver-ai.ru:7724" \
  -H "X-Secret: home-shell-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"cmd":"КОМАНДА"}'
```

## MCP/инструменты на этом компьютере

См. `brain/workstations.md`, раздел "Рабочий ПК" — там зафиксированы все настроенные MCP (notion_home, n8n_mcp) и локальные приложения (vacation-timer, фикс Notion ACL).

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

При сжатии контекста сохранять: текущую задачу, статус проекта, последние грабли, факт что мы на рабочем ПК.
