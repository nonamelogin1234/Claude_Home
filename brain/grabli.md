# ГРАБЛИ — ЗАПОМНИТЬ НАВСЕГДА

## PowerShell / Windows

- `shell:run_command` возвращает null — это нормально, команда выполнилась
- `bash_tool` пишет файлы В КОНТЕЙНЕР, не на ПК → для ПК использовать `Desktop Commander:write_file`
- `bash_tool` НЕ работает для команд на сервере — только через srv.ps1/home.ps1
- `-SkipCertificateCheck` не работает в PowerShell 5 → заменять на `[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }`
- `srv.ps1` ломает сложные команды с кавычками и кириллицей → большие файлы через GitHub → curl
- heredoc через PowerShell не записывается в файл → использовать `python3 -c "open(...).write(...)"`
- **Кириллица в выводе srv.ps1 — кракозябры, это НОРМАЛЬНО. Не пытаться чинить.**

## GitHub

- Блокирует push если в файле есть Google OAuth access_token → передавать через SCP
- Raw кэширует ~10 мин → для срочного деплоя SCP напрямую
- **Редактировать файлы в GitHub — только `github:get_file_contents` + `github:create_or_update_file`**
- При push нескольких файлов сразу — использовать `github:push_files`, лимит ~5 файлов за раз

## Git на локальном компе

- Никогда не клонировать репо ВНУТРЬ другого клонированного репо — будет submodule и git не видит файлы
- Если скачиваешь с GitHub как zip — .git внутри нет, файлы копируются нормально
- Если клонируешь через git clone — внутри будет .git, нельзя вкладывать в другой git репо

## VPS / Docker / n8n

- VPS не резолвит свой домен изнутри → использовать IP 147.45.238.120 напрямую
- `executeCommand` в n8n выполняется ВНУТРИ Docker → всегда HTTP Request → Shell API `http://172.18.0.1:7722`
- wg0 на хосте VPS конфликтует с wg-easy → `sudo wg-quick down wg0 && sudo docker start wg-easy`

## Claude Code

- Claude Code Desktop SSH на Windows — НЕ РАБОТАЕТ, известный баг. Не тратить время.
- `--dangerously-skip-permissions` заблокирован для root → нужен не-root пользователь
- claude авторизуется через OAuth (браузер) — в SSH без port forwarding не работает
- API ключ не подходит если только Pro подписка (нет Console аккаунта)
- Node.js v12 (системный Ubuntu) слишком старый → нужен v20+

## Домашний сервер

- AdGuard Home УДАЛЁН (2026-03-22) — не пытаться переподключать
- SSH с домашнего ПК не работает при включённом WireGuard VPN → отключать WireGuard перед SSH
- SMB шара на русской Windows: "Everyone" не работает → использовать `$env:USERNAME` или "Все"
- Windows локальные пользователи не могут войти по сети из-за политики ForceGuest → фикс: `Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "ForceGuest" -Value 0`
- `$`-переменные nginx (например `$host`) теряются при передаче через home.ps1 → использовать `printf` вместо python3/heredoc
- При записи nginx конфига через `printf` с `\$host` — слэш остаётся буквально в файле → nginx шлёт `Host: \nextcloud...` → Apache 400 Bad Request. Решение: использовать одинарные кавычки в `printf '...$host...'` — тогда shell не трогает `$`, nginx получает правильную переменную
- Сетевой диск, примонтированный в admin PowerShell, НЕ виден в обычном Explorer — `EnableLinkedConnections` не всегда помогает → монтировать через скрипт автозапуска от имени обычного пользователя
- Скорость SMB упирается в 100Мбит (~11 МБ/с) если роутер/порт не гигабитный

## WireGuard (домашний сервер ↔ VPS)

- **ГЛАВНОЕ:** домашний сервер за NAT — ListenPort в конфиге НЕ влияет на внешний порт. Роутер подменяет порт на случайный. WireGuard обновляет endpoint автоматически по входящим пакетам — это штатное поведение.
- **Причина потери туннеля после перезагрузки:** PublicKey пира в wg0.conf домашнего сервера указывал на wg-easy (порт 51820), а не на wg1 (порт 51822) — разные ключи, handshake невозможен криптографически.
- Правильный PublicKey VPS для wg1: `QTSKLBhGyvL+5Sm4EZbnu6m0iL2ufu+8nD3rrIUt00Q=`
- Правильный Endpoint в wg0.conf домашнего: `147.45.238.120:51822`
- На VPS в wg1.conf — НЕ прописывать endpoint для домашнего сервера, WireGuard выучит сам
- `sudo systemctl enable wg-quick@wg1` на VPS — через `ln -s` т.к. `systemctl enable` возвращает stderr и shell-api даёт 500
- Доступ к домашнему серверу — ТОЛЬКО через `home.ps1`, НЕ через `srv.ps1`. Маршрут: nginx VPS :7724 → 10.8.0.27:7722

## Nginx конфиги через srv.ps1

- `printf`, `python3 -c`, heredoc — всё ломает `$host`, `$http_upgrade` при передаче через srv.ps1
- Единственный надёжный способ: base64-кодировать файл локально через PowerShell, передать строку, декодировать на сервере:
  `echo BASE64 | base64 -d > /etc/nginx/sites-available/...`
- Кодировать локально: `[Convert]::ToBase64String([IO.File]::ReadAllBytes('path\to\file'))`
- `mcp__shell__run_command` запускается ЛОКАЛЬНО (WSL), а НЕ на VPS — для VPS только srv.ps1

## VPN / Белые списки РФ

- Cloudflare CDN (оранжевое облако) дросселируется до ~16KB на мобильном интернете РФ → WebSocket туннель устанавливается, но реальный трафик не проходит
- sing-box подключается, показывает "connected", но браузер не работает — обманчивый признак успеха
- DNS через UDP 53 к внешним серверам (8.8.8.8, 1.1.1.1) заблокирован на мобильном в РФ
- Единственное рабочее решение: российский relay-сервер (Yandex Cloud, VK Cloud, Selectel) с whitelisted IP как первый прыжок → Netherlands VPS → интернет
- Схема: `phone → RU relay (whitelisted IP) → VPS NL → internet`
- Cloudflare не является надёжным whitelisted IP для российского мобильного интернета (2026)

## Hevy / Health Connect

- `hevy_sets` — новая таблица (25.03.2026), каждый подход отдельной строкой
- Единицы energy в Health Connect — миллиКалории (mcal), делить на 1000

## Authelia / Homepage

- Порт 3000 на VPS занят Grafana → Homepage запускать на 3030
- Authelia v4.39+: `hash-password` заменена на `authelia crypto hash generate argon2 --password '...'`
- Authelia v4.39+: обязательно добавить `storage.encryption_key` (иначе fatal)
- certbot на VPS сломан (конфликт Python/OpenSSL) → использовать acme.sh --server letsencrypt --webroot /var/www/html
- ZeroSSL (дефолтный CA в acme.sh) отклоняет некоторые поддомены → всегда явно указывать --server letsencrypt
- Cloudflare Tunnel пересоздаёт DNS CNAME даже если удалить запись вручную → удалять домен из Public Hostnames в Zero Trust
- acme.sh --nginx не находит конфиг если домен не в sites-enabled → использовать --webroot
- **"Host validation failed. See logs"** — может приходить от HOMEPAGE, а не Authelia. Homepage требует `HOMEPAGE_ALLOWED_HOSTS=home.myserver-ai.ru` в docker-compose.yml environment, иначе API запросы фронтенда падают с 400
- Authelia /api/configuration всегда отдаёт 403 при запросе с публичного IP сервера (curl изнутри VPS) — это нормально. Браузер через Docker/VPN (172.x.x.x) получает 200 — приватные IP автоматически trusted proxies
- `server.trusted_proxies` в Authelia v4.39+ удалён — не использовать, выдаёт "key not expected"
