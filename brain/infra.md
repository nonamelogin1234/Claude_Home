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
| wg-easy | 51820/51821 | WireGuard VPN (телефон, прочие клиенты) |
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

- **wg1** (порт 51822) — для домашнего сервера, на хосте VPS
- **wg0** (wg-easy контейнер, порт 51820) — телефон и прочие клиенты
- **wg2** (порт 51823) — ⭐ НОВЫЙ (май 2026), для VM Discord-VPN на домашнем ПК, на хосте VPS напрямую (без Docker, чтобы избежать проблем с Docker NAT и UDP)
  - Сервер IP: 10.9.0.1/24, конфиг: `/etc/wireguard/wg2.conf`
  - VM peer public key: `yX1u6fqn0fSOXqfKrawZiw4uv0GL+lLDrX442l+DI3Q=`
  - VM IP в туннеле: 10.9.0.2
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

## 3proxy конфиг (актуальный, май 2026)

Файл: `/etc/3proxy/3proxy.cfg`

```
nscache 65536
timeouts 1 5 30 60 180 1800 15 60
log /var/log/3proxy/3proxy.log D
rotate 30

external 147.45.238.120
internal 0.0.0.0

auth strong
users socks5user:CL:Pr0xy2026!
allow socks5user * * 0-65535
maxconn 1000

socks -p7777 -e147.45.238.120
```

Ключевые настройки:
- `external 147.45.238.120` — реальный IP для UDP ASSOCIATE ответов (без этого Discord голос не работает)
- `internal 0.0.0.0` — слушать на всех интерфейсах
- `-e147.45.238.120` — флаг на строке socks (дублирует external для UDP)
- ⚠️ `ulimits too low (1024)` при maxconn 1000 — нужно поднять через systemd override (`LimitNOFILE=65536`)

---

## ⭐ VM Discord-VPN (НОВОЕ, май 2026)

Виртуальная машина на домашнем ПК для изолированного VPN-окружения.
**Смысл:** Discord + браузер + Claude Code работают через VPN (Нидерланды), игры на хосте — без VPN. Полная сетевая изоляция.

| Параметр | Значение |
|----------|----------|
| Гипервизор | VirtualBox 7.2.8 |
| ОС | Lubuntu 24.04 LTS (EFI, минимальная установка) |
| RAM | 2048 MB |
| CPU | 2 ядра |
| Диск | 25 GB (C:\Users\no-na\VirtualBox VMs\Discord-VPN\) |
| Сеть | NAT (VirtualBox) |
| Пользователь | cthu / 1234 |
| SSH доступ | localhost:2222 → VM:22 |
| SSH ключ | `C:\Users\no-na\.ssh\vm_key` (ed25519, claude@host) |

### Установленный софт в VM

| Программа | Версия | Как запустить |
|-----------|--------|---------------|
| WireGuard | 1.0 | автозапуск, `/etc/wireguard/wg0.conf` |
| Discord | 1.0.138 | меню → Internet → Discord |
| Firefox | встроен | меню → Internet → Firefox |
| Docker | 29.4.3 | `docker ...` |
| Git | 2.43.0 | `git ...` |
| Node.js | v22.22.2 | `node ...` |
| Claude Code CLI | 2.1.141 | `claude` (нужен API ключ при первом запуске) |

### WireGuard в VM

Конфиг: `/etc/wireguard/wg0.conf`
- Подключается к **wg2** на VPS (порт 51823), НЕ к wg-easy
- IP в туннеле: **10.9.0.2**
- DNS: 1.1.1.1
- AllowedIPs: 0.0.0.0/0 (весь трафик VM через VPN)
- PostUp добавляет маршрут к VPS endpoint напрямую (обход петли)

### Управление VM

```powershell
# Запустить
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" startvm "Discord-VPN"

# Выключить
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" controlvm "Discord-VPN" poweroff

# SSH в VM (из домашнего ПК)
ssh -i C:\Users\no-na\.ssh\vm_key -p 2222 cthu@localhost
```

### Важные открытия (май 2026)

- wg-easy (Docker) имеет проблему с UDP NAT — ответы от контейнера не доходят до клиента за двойным NAT
- Решение: wg2 прямо на хосте VPS (без Docker), порт 51823
- Lubuntu 24.04 загружается только в режиме **EFI + ISO на SATA** (BIOS + IDE не работает)
- VirtualBox unattended install не поддерживает Lubuntu (только официальный Ubuntu)
- sudo в VM по SSH требует `-S` флаг: `echo 'пароль' | sudo -S команда`
- Claude Desktop для Linux не существует — используй Claude Code CLI или браузер

---

## Домашний сервер

| Параметр | Значение |
|----------|----------|
| Железо | Maibenben M547, Ryzen 7 4700U, 8GB, NVMe 512GB |
| ОС | Ubuntu Server 24.04, user: sergei, host: homeserver |
| IP сеть | 192.168.0.106 |
| IP WireGuard | 10.8.0.27 |
| Shell API | /home/sergei/shell-api.py, порт 7722 |

## Сервисы на домашнем сервере

| Сервис | Порт | Назначение | Браузер |
|--------|------|------------|---------|
| Immich | 2283 | Фото | https://photos.myserver-ai.ru |
| Nextcloud | 8181 | Облако | https://nextcloud.myserver-ai.ru |
| qbittorrent | 18080→8090 | Торрент | http://192.168.0.106:18080 |
| Jellyfin | 8096 | Медиасервер | http://192.168.0.106:8096 |
| Uptime Kuma | 3001 | Мониторинг | http://192.168.0.106:3001 |

### Samba (сетевые папки)

| Шара | Путь | Доступ | Подключение |
|------|------|--------|-------------|
| Jellyfin | /srv/jellyfin | user: sergei, pass: 7193079a | `\\192.168.0.106\Jellyfin` |
| media | /srv/jellyfin | user: jellyshare | только для Jellyfin-приложений |

**Подключить в Windows:**
```
net use Z: \\192.168.0.106\Jellyfin /user:sergei 7193079a /persistent:yes
```

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

---

## Как подключаться к серверам

### Для Клода — запуск команд на серверах

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

**СПОСОБ 2 — SSH из Bash tool:**
```bash
# VPS:
ssh -o StrictHostKeyChecking=no root@147.45.238.120 "КОМАНДА"

# Домашний сервер через ProxyJump:
ssh -o StrictHostKeyChecking=no -J root@147.45.238.120 sergei@10.8.0.27 "КОМАНДА"

# VM Discord-VPN (с домашнего ПК):
ssh -o StrictHostKeyChecking=no -i C:/Users/no-na/.ssh/vm_key -p 2222 cthu@localhost "КОМАНДА"
```

### SSH ключи (май 2026)

| Ключ | Где лежит | Добавлен в |
|------|-----------|------------|
| user@Useer | домашний ПК (после переустановки Windows — нужно сгенерировать заново) | VPS + домашний сервер |
| torganov-a@work | `C:\Users\torganov-a\.ssh\id_ed25519` | VPS + домашний сервер |
| petro-balt\torganov-a@torganov-alexey | gor-r (bash tool, Claude) | VPS + домашний сервер |
| root@3330663-kd17640 | VPS | домашний сервер |
| claude@host (vm_key) | `C:\Users\no-na\.ssh\vm_key` | VM Discord-VPN (/home/cthu/.ssh/authorized_keys) |

> ⚠️ После переустановки Windows на домашнем ПК — SSH ключ user@Useer утерян, нужно добавить новый в VPS и домашний сервер.

---

## Домашний ПК — инструменты (май 2026, после переустановки Windows)

| Инструмент | Путь / Статус |
|-----------|---------------|
| Python 3.13 | установлен, в PATH ✅ |
| Node.js | v24, в PATH ✅ |
| Git | установлен ✅ |
| Docker | установлен ✅ |
| VirtualBox | 7.2.8, `C:\Program Files\Oracle\VirtualBox\` ✅ |
| WireGuard | установлен, туннель "Allow_all", IP 10.8.0.3 |

### MCP серверы Claude Code (домашний ПК)

Конфиг: `C:\Users\no-na\.claude\settings.json`

| Сервер | Статус | Зависимость |
|--------|--------|-------------|
| desktop-commander | 🟡 Не проверен | Node.js v24 ✅ |
| windows-mcp | 🔴 uvx не установлен | `python -m pip install uv` → `uvx windows-mcp` |

### Proxifier (домашний ПК) — статус: заменён VM-решением

- Прокси: 147.45.238.120:7777, SOCKS5, user: socks5user, pass: Pr0xy2026!
- ⚠️ Proxifier Standard не поддерживает UDP — Discord voice не работает
- ✅ **Актуальное решение:** VM Discord-VPN (VirtualBox) с WireGuard внутри

## Windows zapret / DNS Geohide (май 2026)

Локальное решение на домашнем Windows-ПК для YouTube + Discord без полного VPN:

- Flowseal zapret: `C:\zapret-flowseal\current`
- Служба Windows: `zapret` / display name `zapret Flowseal`
- Автозапуск: `Automatic`
- Выбранная стратегия: `general (ALT).bat`
- Файл выбора стратегии: `C:\zapret-flowseal\current\selected_strategy.txt`
- Проверка здоровья: `C:\zapret-flowseal\current\health_check.cmd`
- Старые no-UAC кнопки управления остались в `C:\Users\no-na\Desktop\tools\zapret-win-bundle\zapret-winws\` и теперь управляют службой `zapret`:
  - `zapret_install_no_uac.cmd`
  - `zapret_start_no_uac.cmd`
  - `zapret_stop_no_uac.cmd`

DNS Geohide `hosts`:

- `C:\Windows\System32\drivers\etc\hosts` скачан из DNS Geohide и нужен для Codex/ChatGPT/OpenAI.
- Этот файл НЕ заменять и НЕ чистить без прямой команды пользователя.
- OpenAI/ChatGPT/Codex домены должны оставаться в `C:\zapret-flowseal\current\lists\list-exclude-user.txt`, чтобы zapret не мешал DNS Geohide.
- Ключевые домены исключений: `chatgpt.com`, `chat.openai.com`, `api.openai.com`, `cdn.oaistatic.com`, `files.oaiusercontent.com`, `codex.openai.com`.

Целевая проверка:

- `zapret` = Running, Automatic
- DNS `chatgpt.com`, `api.openai.com`, `cdn.oaistatic.com` резолвится в DNS Geohide IP (`45.155.204.190` / `37.230.192.51`)
- Discord updater manifest с `updates.discord.com` отвечает JSON
- Discord CDN byte-range отвечает `206`
- YouTube HEAD отвечает `200 OK`

## Telegram Desktop без системного VPN

Цель: Telegram Desktop на Windows должен работать без включения WireGuard и без системных прокси/туннелей, чтобы не ломать браузеры, Codex, Discord, YouTube, DNS Geohide `hosts` и маршруты Windows.

Состояние на конец сессии (май 2026):

- Поднят приватный MTProto proxy на VPS `147.45.238.120`.
- Docker-образ: `telegrammessenger/proxy:latest`.
- Контейнер: `mtproto-proxy`.
- Порт: `9443/tcp` на VPS -> `443/tcp` в контейнере.
- Volume с секретом: `mtproto-proxy-config:/data`.
- Автозапуск: Docker `--restart=always`.
- Ежедневный рестарт для обновления Telegram core IP: `/etc/cron.d/mtproto-proxy-restart`, 04:17 каждый день.
- Проверка в Telegram Desktop: `dd`-secret подключается, но загрузка файлов нестабильна и может зависать; обычный secret без `dd` не подключается.
- Тестовые контейнеры `mtproto-proxy-5222` и `mtproto-proxy-8443` удалены, оставлен только основной `mtproto-proxy` на `9443`.
- Внешний public proxy с `ee` Fake TLS и SNI `yandex.ru` работал заметно лучше, но свой Fake TLS на текущем `telegrammessenger/proxy` не заработал.
- Подключать proxy только внутри Telegram Desktop через `tg://proxy?...` или настройки Telegram.
- Не менять системный proxy Windows.
- Не менять WireGuard.
- Не трогать `C:\Windows\System32\drivers\etc\hosts`.
- Не расширять zapret под Telegram.

Подключение:

- Telegram Desktop -> Settings -> Advanced -> Connection type -> Use custom proxy -> MTProto.
- Server: `147.45.238.120`
- Port: `9443`
- Secret хранится в Docker volume и виден через `docker logs mtproto-proxy`.
- В auto-link из логов порт будет `443`; его нужно вручную заменить на `9443`.
- Для random padding можно пробовать клиентский secret с префиксом `dd` перед основным secret.
- Рабочий вариант был именно с `dd`; без `dd` клиент не подключался.

Проверки:

- `docker ps --filter name=mtproto-proxy`
- `docker logs mtproto-proxy`
- `docker exec mtproto-proxy curl http://localhost:2398/stats`
- С Windows: `Test-NetConnection 147.45.238.120 -Port 9443`

Соображения:

- Порт `443/tcp` на VPS занят nginx, `443/udp` занят sing-box, поэтому proxy вынесен на `9443/tcp`.
- Если возвращаться к теме, перспективнее не обычный `dd` MTProxy, а Fake TLS (`ee`) на `443`; на текущем VPS это требует отдельного обсуждения из-за nginx на `443`.
- Публичные бесплатные MTProto proxy не использовать как основное решение: нестабильно и неизвестно кто владелец.

## Белые списки РФ (наблюдения май 2026)

- При настоящем whitelist-режиме проблема не в протоколе, а в первом прыжке: если IP зарубежного VPS не в белом списке, трафик до него не выйдет.
- DNS/hosts/DoH помогают при DNS-блокировках, но почти бесполезны против whitelist/drop-all.
- Zapret/DPI-desync помогает при DPI-сигнатурах, но не делает зарубежный VPS "белым".
- Устойчивый вариант без покупки готового VPN обычно требует RU relay с доступным/разрешённым IP -> зарубежный VPS -> интернет.
- Тему не развиваем: пользователь решил не запариваться.
