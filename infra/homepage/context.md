# HOMEPAGE + AUTHELIA

## ЦЕЛЬ
Централизованная стартовая страница (Homepage) со всеми сервисами + единая SSO-аутентификация
(Authelia с TOTP) для всех поддоменов myserver-ai.ru. Красивый дизайн, виджеты здоровья и новостей.

## СТАТУС
🟢 Работает — https://home.myserver-ai.ru + https://auth.myserver-ai.ru (2FA TOTP)

## ЧТО СДЕЛАНО
- [2026-04-15] Созданы все файлы: Homepage docker-compose, YAML конфиги (services, settings, widgets)
- [2026-04-15] Создан Authelia: docker-compose, configuration.yml, users_database.yml
- [2026-04-15] Созданы nginx конфиги: homepage, authelia, vaultwarden, music, immich
- [2026-04-15] Создан deploy.sh — полный скрипт деплоя с генерацией секретов и хэша пароля
- [2026-04-15] Деплой на VPS: оба контейнера запущены, SSL через acme.sh (letsencrypt), nginx настроен
- [2026-04-15] TOTP настроен — полный flow аутентификации работает
- [2026-04-15] Исправлена ошибка "Host validation failed" — добавлен HOMEPAGE_ALLOWED_HOSTS=home.myserver-ai.ru
- [2026-04-15] Редизайн: glassmorphism CSS + custom.js развёрнуты на VPS (/opt/homepage/config/)
- [2026-04-15] SSO: nginx для homepage/music/immich/vaultwarden переключён с /api/verify → /api/authz/forward-auth
- [2026-04-15] Authelia сессия: 12h → 168h (неделя), inactivity 2h → 24h
- [2026-04-15] Grok-news сервис: /opt/grok-news/server.py, порт 8770, systemd, nginx /grok-news/
- [2026-04-15] health-stats endpoint: weight=119.2, smoke_days=426, работает
- [2026-04-15] widgets.yaml: customapi виджет здоровья (weight, smoke_days, diff)

## СЛЕДУЮЩИЙ ШАГ
- Добавить виджет погоды (нужен OpenWeatherMap API ключ из Vaultwarden)
- Сменить пароль Authelia (текущий Admin2026! — временный)

## ГРАБЛИ
- Vaultwarden за Authelia ломает мобильные клиенты Bitwarden → при проблемах: policy: bypass для vault
- Navidrome (music) — мобильные клиенты не пройдут через Authelia, при проблемах: bypass
- n8n работает через Cloudflare Tunnel (не через nginx) → Authelia его не затрагивает
- DNS без проксирования Cloudflare (DNS only) — иначе certbot не выдаст сертификат
- `systemctl enable/restart` на VPS возвращает stderr → shell-api даёт 500. Решение: ln -s для enable, start через systemd игнорируя 500
- SSL для home.myserver-ai.ru: /.acme.sh/home.myserver-ai.ru_ecc/fullchain.cer (не /etc/letsencrypt!)
- body_measurements: колонка weight, дата measured_at (не value/date!)
- psql не установлен на VPS → проверять БД через docker exec postgres psql

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Homepage: /opt/homepage/, Docker порт 3030 (внешний), URL: https://home.myserver-ai.ru
- Authelia: /opt/authelia/, Docker порт 9091, URL: https://auth.myserver-ai.ru
- Пользователь Authelia: sergei, email: nonamepogin@gmail.com, группа: admins
- session.domain: myserver-ai.ru (общий для всех поддоменов), expiration: 168h, inactivity: 24h
- Политики: home/vault/photos/music → two_factor; nextcloud → bypass; n8n webhooks → bypass
- Auth endpoint nginx: /api/authz/forward-auth (актуальный для Authelia v4.39+)
- grok-news: /opt/grok-news/server.py, порт 8770, systemd: grok-news.service
- grok-news .env: /opt/grok-news/.env (GROK_API_KEY=...)
- health-stats: GET http://localhost:8770/health-stats → {weight, goal, smoke_days, diff, progress_pct}
- summary: POST http://localhost:8770/summary → {summary, timestamp}
- nginx /grok-news/ location добавлен в homepage конфиг → home.myserver-ai.ru/grok-news/...
- Деплой: cd /opt/homepage && docker compose up -d
- Перезапуск Authelia: docker restart authelia
