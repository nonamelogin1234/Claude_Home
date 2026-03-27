# ДОМАШНИЙ СЕРВЕР

## ЦЕЛЬ
Домашний медиасервер на базе Maibenben M547. Jellyfin для просмотра фильмов, qBittorrent для торрентов, Nextcloud для файлов.

## СТАТУС
🟡 Nextcloud запущен, ждёт DNS записи и SSL сертификата

## ЧТО СДЕЛАНО
- [2026-03-27] Установлен Docker на сервере → работает
- [2026-03-27] Создана папка `/srv/jellyfin` для медиатеки
- [2026-03-27] Запущен Jellyfin в Docker контейнере → доступен на :8096
- [2026-03-27] Установлен и настроен nginx → Jellyfin доступен на http://192.168.0.103 (порт 80)
- [2026-03-27] Настроена Samba на сервере → папка доступна как \\192.168.0.103\Jellyfin
- [2026-03-27] На Windows ПК примонтирован диск Z: → \\192.168.0.103\Jellyfin
- [2026-03-27] Jellyfin настроен, медиатека добавлена (`/media`)
- [2026-03-27] Приложение Jellyfin на телеке подключено, всё работает
- [2026-03-27] Установлен qBittorrent в Docker → порт 8080, работает
- [2026-03-27] Установлен Nextcloud (Docker + MariaDB + Redis) → порт 8181, данные /srv/nextcloud
- [2026-03-27] На VPS: nginx конфиг для nextcloud.myserver-ai.ru (HTTP), установлен acme.sh
- [2026-03-27] Ждёт: DNS A-запись nextcloud → 147.45.238.120 в Cloudflare

## СЛЕДУЮЩИЙ ШАГ
1. Добавить DNS A-запись `nextcloud` → `147.45.238.120` в Cloudflare (DNS only)
2. Запустить acme.sh для SSL: `~/.acme.sh/acme.sh --issue -d nextcloud.myserver-ai.ru --webroot /var/www/certbot`
3. Обновить nginx на VPS до HTTPS конфига
4. Первый вход в Nextcloud, создать admin аккаунт

## ГРАБЛИ
- Диск Z: примонтированный от admin PowerShell не виден в Explorer → монтировать через startup скрипт обычного пользователя
- $-переменные nginx теряются через home.ps1 → использовать printf
- ForceGuest политика блокирует SMB локальных пользователей → отключить через реестр

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Сервер: 192.168.0.103, user: sergei, WireGuard: 10.8.0.27
- Jellyfin: Docker, порт 8096, медиатека: /srv/jellyfin (в контейнере /media)
- qBittorrent: Docker (linuxserver/qbittorrent), порт 8080
- Nextcloud: Docker, порт 8181, данные: /srv/nextcloud/data, DB: /srv/nextcloud/db
  - compose: /srv/nextcloud/docker-compose.yml
  - DB: MariaDB 10.11, user: nextcloud, pass: ncdb2026
  - Redis: включён
  - Env: OVERWRITEPROTOCOL=https, OVERWRITECLIURL=https://nextcloud.myserver-ai.ru
- Nginx домашний: порт 80 → Jellyfin :8096
- VPS nginx: nextcloud.myserver-ai.ru → http://10.8.0.27:8181 (файл: /etc/nginx/sites-enabled/nextcloud)
- acme.sh установлен на VPS в /root/.acme.sh/
- Samba: шара Jellyfin → /srv/jellyfin, пользователь sergei
- Windows диск Z: → \\192.168.0.103\Jellyfin
- Подключение: `powershell -ExecutionPolicy Bypass -File C:\Users\user\home.ps1 -cmd "КОМАНДА"`
