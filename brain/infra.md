# ИНФРАСТРУКТУРА

## VPS myserver-ai.ru

| Параметр | Значение |
|----------|----------|
| IP | 147.45.238.120 |
| ОС | Ubuntu 24.04, Timeweb Нидерланды |
| DNS | 8.8.8.8 статический |

## Docker контейнеры на VPS

| Контейнер | Порт | Назначение |
|-----------|------|------------|
| n8n | 5678 | https://myserver-ai.ru |
| postgres | 5432 | jarvis_memory, user: jarvis, pass: jarvis_pass, IP: 172.18.0.4 |
| vaultwarden | 8081 | https://vault.myserver-ai.ru |
| wg-easy | 51820/51821 | WireGuard VPN |
| tunnel | — | Cloudflare Tunnel |


## Systemd сервисы на VPS

| Сервис | Порт | Назначение |
|--------|------|------------|
| shell-api | 7722→7723 | Shell API (nginx HTTPS proxy) |
| docai | 8765 | RAG поиск по PDF |
| kinoclaude | 8766→8767 | KinoClaude MCP |
| 3proxy | 7777 | SOCKS5 прокси |
| sing-box | 10080/TCP (WS), 2083/TCP (Reality), 443/UDP (Hysteria2) | VPN — 3 протокола, см. VPN_Hide/context.md |
| zabbix-agent | — | Мониторинг (агент) |
| nginx | 80/443/7723/7724/8767 | Reverse proxy |

## WireGuard

- wg1 (порт 51822) — для домашнего сервера, на хосте VPS
- wg0 (wg-easy контейнер, порт 51820) — телефон и прочие клиенты
- ⚠️ wg0 на хосте НЕ должен быть поднят — конфликт с wg-easy

## Nginx маршруты

| Домен / Путь | Куда | Примечание |
|---|---|---|
| myserver-ai.ru | n8n (Cloudflare Tunnel) | |
| myserver-ai.ru/docs | docai :8765 | |
| mcp.myserver-ai.ru:443 | :8080 | cadvisor (Docker мониторинг) |
| mcp.myserver-ai.ru:7723 | shell-api :7722 HTTPS | VPS shell |
| mcp.myserver-ai.ru:7724 | home shell-api :7722 через wg1 | Домашний сервер shell API |
| mcp.myserver-ai.ru:8767/sse, /messages | kinoclaude :8766 HTTPS | |
| vault.myserver-ai.ru | vaultwarden :8081 | |
| photos.myserver-ai.ru | 10.8.0.27:2283 | Immich на домашнем сервере |
| nextcloud.myserver-ai.ru | 10.8.0.27:8181 | Nextcloud на домашнем сервере |
| vpn.myserver-ai.ru/vpn/ | :10080 | sing-box VPN (WebSocket) |


## Домашний сервер

| Параметр | Значение |
|----------|----------|
| Железо | Maibenben M547, Ryzen 7 4700U, 8GB, NVMe 512GB |
| ОС | Ubuntu Server 24.04, user: sergei, host: homeserver |
| IP сеть | 192.168.0.106 |
| IP WireGuard | 10.8.0.27 |
| Shell API | /home/sergei/shell-api.py, порт 7722 |

## Сервисы на домашнем сервере

| Сервис | Порт | Назначение |
|--------|------|------------|
| Immich | 2283 | Фото (https://photos.myserver-ai.ru) |
| Nextcloud | 8181 | Облако (https://nextcloud.myserver-ai.ru) |
| qbittorrent | 18080→8090 | Торрент |
| Jellyfin | 8096 | Медиасервер |

## PostgreSQL — таблицы jarvis_memory

| Таблица | Содержимое |
|---------|------------|
| finance_transactions | Транзакции из SMS (Фёдор) |
| finance_chat_memory | Память чата Фёдора |
| body_measurements | Весы Picooc |
| health_daily_summary | Health Connect: шаги, сон, пульс, тренировки |
| hevy_workouts | Тренировки Hevy (агрегат) |
| hevy_sets | Детальные сеты Hevy (каждый подход, с 25.03.2026) |
| doc_chunks, doc_numbers, doc_metadata | DocAI (pgvector) |

## n8n Workflows

| ID | Название | Назначение |
|----|----------|------------|
| aWsvhTmHxhGtoHJ7 | Finance v2 Фёдор | SMS → PostgreSQL → Telegram |
| jFfWpwLHTHINxNwd | Work_Letters | Рабочие письма |
| CUZeNQIDJRD9ldxy | Alice→Claude | Алиса → n8n → Claude |
| 01BCs4rVxAKdi01J | Health Connect sync | Drive → Postgres, 7:30 МСК |
| pWp8TqJNVngiOOVZ | Hevy sync | workout_data.csv → Postgres, /6h |

## Как подключаться к серверам

### Для Клода — запуск команд на серверах (апрель 2026, всё протестировано)

**СПОСОБ 1 — curl напрямую (самый быстрый, из Bash tool):**
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

**СПОСОБ 2 — SSH напрямую из Bash tool (без PowerShell, ключ gor-r прописан):**
```bash
# VPS:
ssh -o StrictHostKeyChecking=no root@147.45.238.120 "КОМАНДА"

# Домашний сервер через ProxyJump:
ssh -o StrictHostKeyChecking=no -J root@147.45.238.120 sergei@10.8.0.27 "КОМАНДА"
```

**СПОСОБ 3 — PowerShell скрипты (тоже работают):**
```powershell
# VPS — рабочий ПК:
powershell -ExecutionPolicy Bypass -File C:\Users\torganov-a\srv.ps1 -cmd "КОМАНДА"
# Домашний сервер — рабочий ПК:
powershell -ExecutionPolicy Bypass -File C:\Users\torganov-a\home.ps1 -cmd "КОМАНДА"
# VPS — домашний ПК:
powershell -ExecutionPolicy Bypass -File C:\Users\user\srv.ps1 -cmd "КОМАНДА"
# Домашний сервер — домашний ПК:
powershell -ExecutionPolicy Bypass -File C:\Users\user\home.ps1 -cmd "КОМАНДА"
```

> Shell API секреты: VPS = `shell-api-secret-2026`, домашний = `home-shell-secret-2026`
> Порты: VPS shell-api :7722 → nginx HTTPS :7723, домашний :7722 → nginx HTTPS :7724
> home.ps1 есть на ОБОИХ ПК (рабочий и домашний).

### SSH — терминал для Сергея

**SSH конфиг настроен** на рабочем ПК (`C:\Users\torganov-a\.ssh\config`).
Просто открыть cmd/PowerShell и ввести:
```
ssh vps          # → VPS (root), без пароля
ssh homeserver   # → домашний сервер (sergei), через VPS, без пароля
```

**С домашнего ПК** (локальная сеть):
```bash
ssh sergei@192.168.0.106   # прямо, без VPS
```
> Если WireGuard VPN включён — отключи перед подключением.

**С рабочего ПК вручную (если config не работает):**
```
ssh -i C:\Users\torganov-a\.ssh\id_ed25519 root@147.45.238.120
ssh -i C:\Users\torganov-a\.ssh\id_ed25519 -J root@147.45.238.120 sergei@10.8.0.27
```

### SSH ключи (апрель 2026)

| Ключ | Где лежит | Добавлен в |
|------|-----------|------------|
| user@Useer | домашний ПК | VPS + домашний сервер |
| torganov-a@work | `C:\Users\torganov-a\.ssh\id_ed25519` | VPS + домашний сервер |
| petro-balt\torganov-a@torganov-alexey | gor-r (bash tool, Claude) | VPS + домашний сервер |
| root@3330663-kd17640 | VPS | домашний сервер |

> Порт 7724 — это shell API домашнего сервера, НЕ SSH.

## Proxifier (домашний ПК)

- Прокси: 147.45.238.120:7777, SOCKS5, user: socks5user, pass: Pr0xy2026!
- Discord.exe → через прокси. Telegram → прокси в настройках. Default → Direct
