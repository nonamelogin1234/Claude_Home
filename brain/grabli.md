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
- Если Docker на VPS не может скачать образ и пишет `lookup registry-1.docker.io on [::1]:53: connection refused` — проверить `/etc/resolv.conf`. В мае 2026 он оказался пустым symlink на resolvconf при выключенном `systemd-resolved`; исправлено статическим `/etc/resolv.conf` с `8.8.8.8` и `1.1.1.1`.
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
- OpenClaw на homeserver: Telegram API напрямую с домашнего сервера таймаутится. Решение: HTTP proxy на VPS через WireGuard `10.8.0.1:7779` (3proxy `proxy -p7779 -i10.8.0.1 -e147.45.238.120`) + `OPENCLAW_PROXY_URL` в `/home/sergei/.openclaw/openclaw.env`.
- OpenClaw Telegram polling: должен работать только один gateway на одного Telegram-бота. После переноса на homeserver выключить Windows gateway, иначе polling/статусы могут конфликтовать.
- OpenClaw не должен развиваться как ежедневный девопс-мониторинг. Главная продуктовая рамка: личный секретарь Сергея в Telegram; серверные проверки — только один из инструментов и в основном по запросу.
- SSH с домашнего ПК не работает при включённом WireGuard VPN → отключать WireGuard перед SSH
- SMB шара на русской Windows: "Everyone" не работает → использовать `$env:USERNAME` или "Все"
- Windows локальные пользователи не могут войти по сети из-за политики ForceGuest → фикс: `Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "ForceGuest" -Value 0`
- `$`-переменные nginx (например `$host`) теряются при передаче через home.ps1 → использовать `printf` вместо python3/heredoc
- При записи nginx конфига через `printf` с `\$host` — слэш остаётся буквально в файле → nginx шлёт `Host: \nextcloud...` → Apache 400 Bad Request. Решение: использовать одинарные кавычки в `printf '...$host...'` — тогда shell не трогает `$`, nginx получает правильную переменную
- Сетевой диск, примонтированный в admin PowerShell, НЕ виден в обычном Explorer — `EnableLinkedConnections` не всегда помогает → монтировать через скрипт автозапуска от имени обычного пользователя
- Скорость SMB упирается в 100Мбит (~11 МБ/с) если роутер/порт не гигабитный
- **qBittorrent съедает до 2.5GB RAM** — при зависаниях Jellyfin проверять `docker stats` и рестартовать qBittorrent

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

## Windows zapret / DNS Geohide

- `C:\Windows\System32\drivers\etc\hosts` может быть файлом DNS Geohide и нужен для Codex/ChatGPT/OpenAI. Не заменять, не чистить Google/OpenAI-записи и не делать `ipconfig /flushdns` как универсальный фикс без причины.
- Если DNS Geohide `hosts` прибивает ChatGPT/OpenAI к своим IP, VPN может не помочь: Windows всё равно использует IP из `hosts`. Для режима “OpenAI через VPN” Geohide-hosts нужно временно убирать/отключать.
- Скачанный вручную `Downloads\hosts` DNS Geohide может устаревать. Для режима "ChatGPT/Codex без VPN" использовать только ярлык `Включить обход` (`enable_bypass.cmd`), он скачивает свежий hosts с GitHub `Internet-Helper/GeoHideDNS`, обновляет zapret и чистит DNS. Старый OpenAI-блок (`45.155.204.190` / `37.230.192.51`) ломал ChatGPT/Codex.
- Не плодить ярлыки управления zapret/GeoHide. На рабочем столе должны быть только `Включить обход`, `Выключить обход`, `Добавить сайт в обход`; остальные проверки запускать из `C:\zapret-flowseal\current` при необходимости.
- Исключение к правилу про ярлыки: `Монитор доступа` допустим как отдельная кнопка, потому что он ничего не меняет в zapret/hosts и нужен для живого статуса Codex/ChatGPT/OpenAI.
- `codex.openai.com` не резолвится и не является основной точкой входа. Codex web живёт на `chatgpt.com/codex`; для него важны `chatgpt.com` и WebSocket на `chatgpt.com`, а не отдельный `codex.openai.com`.
- При настройке zapret для Discord/YouTube обязательно держать OpenAI/ChatGPT/Codex домены в `C:\zapret-flowseal\current\lists\list-exclude-user.txt`, иначе можно сломать работу Codex даже при включённом VPN.
- Edge может продолжать ломать Google после изменения QUIC/hosts/zapret из-за фонового процесса и сетевого кэша профиля. Мягкий фикс без удаления профиля: закрыть все `msedge.exe`, сделать бэкап `Local State` и `Default\Preferences`, удалить только `Default\Cache`, `Default\Code Cache`, `Default\GPUCache`, `Default\DawnGraphiteCache`, `Default\DawnWebGPUCache`, `Default\Network Action Predictor*`, затем `ipconfig /flushdns` и заново открыть Edge.
- Для Flowseal zapret на Windows текущая рабочая служба одна: `zapret`. Старые `winws1/winws2` считать мусором и не использовать как целевое состояние.
- Проверять не только YouTube, но и Discord updater: `updates.discord.com` должен отдавать manifest JSON, а Discord CDN byte-range должен отвечать `206`.
- Если HTTPS сайта после добавления домена даёт `Recv failure: Connection was reset`, проблема может быть не в списке, а в стратегии. 2026-05-21 для Pornhub сработала `general (ALT11).bat`; `general (ALT).bat` сбрасывал TLS.
- Не срезать `www.` автоматически в zapret hostlist: для некоторых сайтов нужны явные `www.*` и redirect-домены (`rt.pornhub.org`), иначе основной домен может пройти, а редирект/браузер — нет.
- Google Flow: `labs.google` должен быть в DNS Geohide `hosts`, а `flow.google` НЕ добавлять в hosts. `flow.google` на GeoHide IP даёт TLS reset; рабочая схема — обычный DNS для `flow.google` → редирект на `https://labs.google/fx/tools/flow`, где `labs.google` уже идёт через GeoHide.
- Firefox может зависать на Google/GeoHide из-за собственного DoH Mozilla/Cloudflare и HTTP/3. Фикс в профиле: `network.trr.mode=5`, `doh-rollout.self-enabled=false`, `doh-rollout.mode=5`, `network.http.http3.enabled=false`, затем полный перезапуск Firefox.

## IKEv2 VPN (strongSwan) на Samsung Android

- Samsung Android 12+ показывает только 4 типа VPN: IKEv2/IPSec MSCHAPv2, PSK, RSA, EAP-TLS — XAuth PSK и L2TP убраны
- `hwdsl2/ipsec-vpn-server` (Libreswan) использует `ikev2=never` по умолчанию и не поддерживает EAP-MSCHAPv2 — не подходит для Samsung
- `philplckthun/strongswan` — рабочий образ, поддерживает EAP-MSCHAPv2 для Samsung
- **IKEv2 EAP-MSCHAPv2 требует сертификат сервера** — без `leftcert` strongSwan говорит `no private key found` и рвёт соединение
- При пересоздании контейнера (`docker rm + docker run`) сертификаты уничтожаются — их надо генерировать заново И обновлять CA на телефоне
- Контейнер перезаписывает `/etc/ipsec.secrets` при каждом старте → RSA ключ нужно добавлять ПОСЛЕ запуска через `docker exec` + `ipsec rereadsecrets`
- `/run.sh` в philplckthun/strongswan создаёт несколько conn-ов — нужно заменить `/etc/ipsec.conf` на чистый, иначе strongSwan выбирает неправильный conn
- Для рабочего IKEv2 EAP нужен чистый конфиг: только один conn `ikev2-eap-mschapv2` с `leftauth=pubkey`, `leftcert=`, `rightauth=eap-mschapv2`, `eap_identity=%identity`
- **Главная грабля с нет интернета:** на Ubuntu 24.04 Docker использует nftables, а strongSwan добавляет правила в iptables-legacy. Это разные наборы правил. Нужно добавлять FORWARD и POSTROUTING в **nftables** (`nft insert rule ip filter FORWARD ip saddr 10.0.2.0/24 accept` и т.д.)
- nftables FORWARD chain имеет `policy drop` + правила Docker. Новые правила `nft add rule` добавляются ПОСЛЕ встроенного `drop` → надо `nft insert rule` (вставить В НАЧАЛО)
- После добавления правил в nftables FORWARD трафик пойдёт и nftables POSTROUTING MASQUERADE заработает
- rp_filter на проблему не влияет если уже = 0
- VPN адрес пула: 10.0.2.0/24, шлюз клиентам: 8.8.8.8 DNS
- **nftables правила не переживают ребут** — нужно прописывать в `/etc/nftables.conf` или скрипт при старте контейнера

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
- SSL для home.myserver-ai.ru выдан через acme.sh, лежит в `/.acme.sh/home.myserver-ai.ru_ecc/` — НЕ в /etc/letsencrypt/
- `systemctl enable/restart/start` на VPS выдают что-то в stderr → shell-api даёт HTTP 500. Но команда выполняется. Для enable: `ln -sf ... /etc/systemd/system/multi-user.target.wants/`. Для start: игнорировать 500, проверять через `curl health`.
- body_measurements таблица: колонки `weight` и `measured_at` (НЕ value/date). psql нет на хосте → проверять через `docker exec postgres psql`
- Authelia v4.39+: `/api/authz/forward-auth` возвращает 400 при nginx auth_request (не передаёт нужные заголовки корректно) → использовать `/api/verify` с `X-Original-URL`, он deprecated но работает стабильно
- Open-Meteo (api.open-meteo.com) — бесплатная погода без API ключа. СПб: lat=59.9386, lon=30.3141

## Homepage custom.js (2026-04-15)

- Homepage v1.12.3 **не загружает custom.js автоматически** — только custom.css. Нужен nginx `sub_filter '</head>' '<script defer src="/api/config/custom.js"></script></head>'` + `proxy_set_header Accept-Encoding ""` (иначе gzip сломает sub_filter) + `sub_filter_once on`
- `waitFor('main', init)` стреляет ДО гидрации React → React при гидрации стирает вставленный DOM. Не использовать.
- `waitFor('#services-list', ...)` — ID `#services-list` НЕ существует в Homepage v1.12.3. waitFor тихо падает через 6 секунд ничего не вызвав.
- **Правильный подход:** `window.addEventListener('load', function() { setTimeout(init, 300); })` — к этому моменту React гарантированно завершил гидрацию
- Для диагностики JS на странице — открывать DevTools → Console, смотреть ошибки и `console.log`. Удалённая диагностика через curl ненадёжна — curl не выполняет JS.
- Если JS всё равно не работает после window.onload — следующий шаг: открыть DevTools → Elements и проверить реальную структуру DOM (какие ID/классы есть в `<main>` после загрузки)
