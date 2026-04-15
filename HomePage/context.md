# HOMEPAGE + AUTHELIA

## ЦЕЛЬ
Централизованная стартовая страница (Homepage) со всеми сервисами + единая SSO-аутентификация
(Authelia с TOTP) для всех поддоменов myserver-ai.ru.

## СТАТУС
🟢 Работает — всё защищено, осталось настроить TOTP

## ЧТО СДЕЛАНО
- [2026-04-15] Созданы все файлы: Homepage docker-compose, YAML конфиги (services, settings, widgets)
- [2026-04-15] Создан Authelia: docker-compose, configuration.yml, users_database.yml
- [2026-04-15] Созданы nginx конфиги: homepage, authelia, vaultwarden (с auth), music (с auth), immich (с auth)
- [2026-04-15] Homepage запущен на порту 3030 (порт 3000 занят Grafana)
- [2026-04-15] Authelia запущена на порту 9091, исправлена для v4.39 (encryption_key)
- [2026-04-15] SSL получен через acme.sh --server letsencrypt --webroot для home + auth
- [2026-04-15] Все сервисы защищены: home/vault/photos/music → 302 на auth.myserver-ai.ru

## СЛЕДУЮЩИЙ ШАГ
1. Зайти на https://auth.myserver-ai.ru
2. Авторизоваться: логин sergei, пароль Admin2026!
3. Настроить TOTP (сканировать QR в Google Authenticator / Aegis)
4. После настройки TOTP — сменить пароль Admin2026!:
   `docker run --rm authelia/authelia:latest authelia crypto hash generate argon2 --password 'НОВЫЙ_ПАРОЛЬ'`
   вставить хэш в /opt/authelia/config/users_database.yml и делать docker restart authelia

## ГРАБЛИ
- Порт 3000 занят Grafana → Homepage запущен на 3030
- Authelia v4.39 требует storage.encryption_key (deprecated синтаксис server.host/port)
- certbot сломан (Python конфликт) → использовать acme.sh --server letsencrypt --webroot
- home.myserver-ai.ru был в Cloudflare Tunnel (cfargotunnel CNAME) → нужно удалить из Public Hostnames в Zero Trust
- ZeroSSL отклоняет auth.myserver-ai.ru → обязательно --server letsencrypt
- Vaultwarden за Authelia сломает мобильные клиенты/расширения — при проблемах см. ниже
- Navidrome (music) — аналогично, мобильные клиенты не пройдут через Authelia
- n8n работает через Cloudflare Tunnel, не через nginx → Authelia его не защищает

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Homepage: /opt/homepage/, порт 3030, URL: https://home.myserver-ai.ru
- Authelia: /opt/authelia/, порт 9091, URL: https://auth.myserver-ai.ru
- Пользователь: sergei / Admin2026! (сменить после настройки TOTP)
- SSL: /.acme.sh/home.myserver-ai.ru_ecc/ и /.acme.sh/auth.myserver-ai.ru_ecc/
- Политики: home/vault/photos/music → two_factor; nextcloud → bypass; n8n webhooks → bypass
- Перезапуск Homepage: cd /opt/homepage && docker compose up -d
- Перезапуск Authelia: docker restart authelia
- Отключить Authelia для домена (bypass): редактировать /opt/authelia/config/configuration.yml
