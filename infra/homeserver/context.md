# ДОМАШНИЙ СЕРВЕР

## ЦЕЛЬ
Домашний медиасервер на базе Maibenben M547. Jellyfin для просмотра фильмов, qBittorrent для торрентов, Nextcloud для файлов.

## СТАТУС
🟢 Immich установлен, HTTPS работает, доступен на https://photos.myserver-ai.ru

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
- [2026-03-27] DNS A-запись nextcloud → 147.45.238.120 добавлена в Cloudflare (DNS only)
- [2026-03-27] SSL сертификат получен через acme.sh (Let's Encrypt) → /.acme.sh/nextcloud.myserver-ai.ru_ecc/
- [2026-03-27] nginx на VPS настроен на HTTPS → Nextcloud доступен на https://nextcloud.myserver-ai.ru
- [2026-03-28] Подключён HDD 1TB USB → /srv/hdd, ext4, UUID в fstab (nofail)
- [2026-03-28] Установлен Immich (Docker Compose) → порт 2283, хранилище /srv/hdd/immich
- [2026-03-28] SSL + nginx на VPS → Immich доступен на https://photos.myserver-ai.ru

## СЛЕДУЮЩИЙ ШАГ
- Первый вход: https://photos.myserver-ai.ru — создать admin аккаунт
- Установить мобильное приложение Immich, настроить автобэкап фото

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
- acme.sh: установлен в /.acme.sh/, сертификаты в /.acme.sh/*_ecc/, установлены в /etc/nginx/ssl/
- Immich: Docker Compose в /srv/immich/docker-compose.yml, БД: /srv/immich/db
  - Хранилище фото: /srv/hdd/immich (HDD 1TB)
  - DB: PostgreSQL (pgvecto-rs), user: immich, pass: immich_pass_2026
  - VPS nginx: photos.myserver-ai.ru → http://10.8.0.27:2283 (файл: /etc/nginx/sites-enabled/immich)
  - client_max_body_size: 50000m, proxy_read_timeout: 600s
- Samba: шара Jellyfin → /srv/jellyfin, пользователь sergei
- Windows диск Z: → \\192.168.0.103\Jellyfin
- Подключение: `powershell -ExecutionPolicy Bypass -File C:\Users\user\home.ps1 -cmd "КОМАНДА"`
