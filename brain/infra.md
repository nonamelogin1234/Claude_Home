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
| 3proxy | 8443 | SOCKS5 прокси |
| sing-box | 10080 | VPN (sing-box), доступен через vpn.myserver-ai.ru/vpn/ |
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
| mcp.myserver-ai.ru:443 | :8080 | ⚠️ что за :8080 — уточнить |
| mcp.myserver-ai.ru:7723 | shell-api :7722 HTTPS | VPS shell |
| mcp.myserver-ai.ru:7724 | home shell-api :7722 через wg1 | Домашний сервер |
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
| IP сеть | 192.168.0.103 |
| IP WireGuard | 10.8.0.27 |
| Shell API | /home/sergei/shell-api.py, порт 7722 |

## Сервисы на домашнем сервере

| Сервис | Порт | Назначение |
|--------|------|------------|
| Immich | 2283 | Фото (https://photos.myserver-ai.ru) |
| Nextcloud | 8181 | Облако (https://nextcloud.myserver-ai.ru) |

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

```powershell
# VPS — домашний ПК:
powershell -ExecutionPolicy Bypass -File C:\Users\user\srv.ps1 -cmd "КОМАНДА"
# VPS — рабочий ПК:
powershell -ExecutionPolicy Bypass -File C:\Users\torganov-a\srv.ps1 -cmd "КОМАНДА"
# Домашний сервер:
powershell -ExecutionPolicy Bypass -File C:\Users\user\home.ps1 -cmd "КОМАНДА"
```

Shell API напрямую:
```
POST https://mcp.myserver-ai.ru:7723
X-Secret: shell-api-secret-2026
{"cmd": "команда"}
```

## Proxifier (домашний ПК)

- Прокси: 147.45.238.120:8443, SOCKS5, user: socks5user, pass: Pr0xy2026!
- Discord.exe → через прокси. Telegram → прокси в настройках. Default → Direct
