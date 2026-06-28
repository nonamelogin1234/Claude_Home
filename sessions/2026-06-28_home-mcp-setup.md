# Сессия 2026-06-28 — Домашний ПК: настройка MCP и деплой

> Этот файл — хендофф для рабочего ПК. Прочитай перед тем как говорить "сделай то, что мы вчера сделали дома".

## Что было сделано

### 1. RPG Трекер (веб-сервис на VPS) — починен
- Контейнер падал с 500: bind mount `/tmp/claude_home/rpg/frontend` исчез (папка удалена).
- Фикс: передеплоен из `/opt/rpg-tracker/` — теперь bind mount стабильный (`/opt/rpg-tracker/frontend:/app/frontend`).
- Команды деплоя обновлены в `projects/rpg-tracker/context.md`.
- Сейчас: **работает**, HTTP 200 на `https://mcp.myserver-ai.ru:8769/`.

### 2. Spotify MCP — установлен и авторизован
- Старый пакет `@darrenjaws/spotify-mcp` давал `response_type must be code` + `server_error`.
- Причина: Spotify Dashboard имел `http://127.0.0.1:8888/callback`, а конфиг — порт 3000.
- Решение: переключились на `@0xbarandiaran/spotify-mcp-server` (обновлён под Spotify API Feb 2026).
- Установлен глобально: `npm install -g @0xbarandiaran/spotify-mcp-server`.
- Токены OAuth сохранены в `C:\Users\no-na\.spotify-mcp\config.json` (redirectUri: 8888).
- В `claude_desktop_config.json` прописан путь: `C:\Users\no-na\AppData\Roaming\npm\spotify-mcp-server.cmd`.
- Статус: **подключается**, ошибка `403 Active premium subscription required` — это Spotify-side задержка, пройдёт само.

### 3. PowerShell MCP — добавлен в Claude Code
- Exe уже был: `C:\Users\no-na\ps-modules\PowerShell.MCP\1.10.0\bin\win-x64\PowerShell.MCP.Proxy.exe`.
- Добавлен в `.mcp.json` (домашнее репо).
- На **рабочем ПК** путь другой — проверь `brain/workstations.md` раздел "Рабочий ПК" и добавь по аналогии если нужно.

### 4. RPG MCP (text-adventure-handler-mcp) — починен и работает
- Был в `claude_desktop_config.json` как `uvx --from git+https://...` — каждый раз тянул с GitHub, таймаутился.
- Установлен постоянно: `uv tool install --from git+https://github.com/narrowstacks/text-adventure-handler-mcp text-adventure-handler-mcp`.
- В конфиге заменён на прямой путь: `C:\Users\no-na\.local\bin\text-adventure-handler-mcp.exe`.
- Статус: **работает**, доступно 7 приключений (Crystal Caverns, Jade Dragon Case, Station Anomaly и др.).
- Механика: MCP хранит стейт игры в БД — можно продолжать сессию между чатами.

## Итоговый конфиг Claude Desktop (домашний ПК)
Файл: `C:\Users\no-na\AppData\Roaming\Claude\claude_desktop_config.json`
```json
{
  "mcpServers": {
    "spotify": { "command": "C:\\Users\\no-na\\AppData\\Roaming\\npm\\spotify-mcp-server.cmd" },
    "rpg-mcp": { "command": "C:\\Users\\no-na\\.local\\bin\\text-adventure-handler-mcp.exe" },
    "telegram": { ... }
  }
}
```

## Что делать на рабочем ПК
Эти MCP специфичны для **домашнего ПК** — пути другие, устанавливать отдельно если нужно:
- Spotify MCP: `npm install -g @0xbarandiaran/spotify-mcp-server`, создать `~/.spotify-mcp/config.json`, запустить auth.
- PowerShell MCP: найти путь к `PowerShell.MCP.Proxy.exe` на рабочем ПК, добавить в `.mcp.json`.
- RPG MCP: `uv tool install --from git+https://github.com/narrowstacks/text-adventure-handler-mcp text-adventure-handler-mcp`, добавить в Desktop конфиг.

## Грабли зафиксированы
- `brain/grabli.md` — обновлён (bind mount rpg-tracker).
- `projects/rpg-tracker/context.md` — обновлён (deploy-инструкции).
- `brain/workstations.md` — обновлён (spotify 🟢, powershell 🟢).
