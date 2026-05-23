# 2026-05-23 — VPS Timeweb recovery

## Что произошло

- WireGuard VPN перестал работать с ПК и телефона.
- Диагностика показала полную недоступность VPS `147.45.238.120`: SSH, HTTPS, shell-api и WireGuard-порты не отвечали.
- В панели Timeweb сервер `Diligent Sagittarius` был выключен.
- Причина: авария питания/восстановление сервисов Timeweb в зоне `ams-1`.

## Что сделали

- Восстановлены локальные обертки:
  - `C:\Users\no-na\srv.ps1` для VPS shell-api.
  - `C:\Users\no-na\home.ps1` для homeserver shell-api через VPS.
  - `C:\Users\no-na\timeweb-vps.ps1` для аварийного управления Timeweb API.
- Timeweb server id зафиксирован: `3330663`.
- VPS был запущен через Timeweb API. HTTP-запрос вернул timeout, но команда сработала и сервер поднялся.
- После старта обнаружен конфликт WireGuard: `wg-quick@wg0` был поднят на хосте VPS, хотя `wg0` должен принадлежать контейнеру `wg-easy`.
- Исправлено:
  - `wg-quick@wg0` остановлен и отключен из автозапуска.
  - `wg1` перезапущен через systemd и стал `active`.
  - `wg2` остался `active`.
  - `wg-easy` healthy, клиенты дают fresh handshakes.
- Проверено:
  - `nginx`, `docker`, `shell-api` active.
  - `vault.myserver-ai.ru` отвечает `200`.
  - `myserver-ai.ru` отвечает `200`.
  - `mcp.myserver-ai.ru:7723` доступен.

## Доступы

- Timeweb API ключ добавлен в Vaultwarden item `API-timeweb.cloud`, поле `token`.
- Для аварийного доступа без живого Vaultwarden создан DPAPI-резерв:
  - `C:\Users\no-na\.codex-secrets\timeweb-token.dpapi`
  - Читается только под Windows-пользователем `no-na`.
- `timeweb-vps.ps1` берет токен в порядке:
  1. `TIMEWEB_CLOUD_TOKEN`
  2. DPAPI-файл
  3. Vaultwarden item `API-timeweb.cloud` / field `token`
- `timeweb-vps.ps1 -action status` редактирует чувствительные поля перед выводом.

## Найденные локальные файлы

- `STARTUP.md` и `codex-start.ps1` — стартовый протокол Codex Home, создан ранее при переезде в Codex.
- `.agents/mcp/vaultwarden_secrets_mcp.py` — локальный MCP-сервер Vaultwarden, подключен в `C:\Users\no-na\.codex\config.toml`.
- `.agents/mcp/vaultwarden-secrets.allowlist.example.json` — пример allowlist.

## Следующий старт

- Если снова упадет VPS: использовать `C:\Users\no-na\timeweb-vps.ps1 -action status -serverId 3330663`, затем `-action start`.
- После старта проверять `wg-quick@wg0` должен быть `inactive/disabled`, `wg1/wg2` — `active/enabled`, `wg-easy` — healthy.
