# HOMEPAGE + AUTHELIA

## ЦЕЛЬ
Централизованная стартовая страница (Homepage) со всеми сервисами + единая SSO-аутентификация
(Authelia с TOTP) для всех поддоменов myserver-ai.ru.

## СТАТУС
🟢 Работает — https://home.myserver-ai.ru + https://auth.myserver-ai.ru (2FA TOTP)

## ЧТО СДЕЛАНО
- [2026-04-15] Созданы все файлы: Homepage docker-compose, YAML конфиги (services, settings, widgets)
- [2026-04-15] Создан Authelia: docker-compose, configuration.yml (с плейсхолдерами секретов), users_database.yml
- [2026-04-15] Созданы nginx конфиги: homepage, authelia, vaultwarden (с auth), music (с auth), immich (с auth)
- [2026-04-15] Создан deploy.sh — полный скрипт деплоя с генерацией секретов и хэша пароля
- [2026-04-15] Деплой на VPS: оба контейнера запущены, SSL через acme.sh (letsencrypt), nginx настроен
- [2026-04-15] TOTP настроен — полный flow аутентификации работает
- [2026-04-15] Исправлена ошибка "Host validation failed" — добавлен HOMEPAGE_ALLOWED_HOSTS=home.myserver-ai.ru в docker-compose

## СЛЕДУЮЩИЙ ШАГ
- Сменить пароль Authelia (текущий Admin2026! — временный)
- Опционально: виджет с новостями через n8n + Grok API

## ГРАБЛИ
- Vaultwarden за Authelia сломает мобильные клиенты Bitwarden/расширения — они используют API, не браузерные сессии.
  При проблемах: поставить `policy: bypass` для vault.myserver-ai.ru в /opt/authelia/config/configuration.yml
- Navidrome (music) то же самое — десктопные/мобильные клиенты не пройдут через Authelia
- n8n работает через Cloudflare Tunnel (не через nginx) → Authelia nginx-уровня его не затрагивает напрямую
- DNS должен быть без проксирования Cloudflare (DNS only) — иначе certbot не выдаст сертификат

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Homepage: /opt/homepage/, Docker порт 3000, URL: https://home.myserver-ai.ru
- Authelia: /opt/authelia/, Docker порт 9091, URL: https://auth.myserver-ai.ru
- Пользователь Authelia: sergei, email: nonamepogin@gmail.com, группа: admins
- session.domain: myserver-ai.ru (общий для всех поддоменов)
- Политики: home/vault/photos/music → two_factor; nextcloud → bypass; n8n webhooks → bypass
- Деплой: cd /opt/homepage && docker compose up -d
- Перезапуск Authelia: docker restart authelia
- Проверка конфига: nginx -t && systemctl reload nginx
