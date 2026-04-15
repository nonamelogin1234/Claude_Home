# HOMEPAGE + AUTHELIA

## ЦЕЛЬ
Централизованная стартовая страница (Homepage) со всеми сервисами + единая SSO-аутентификация
(Authelia с TOTP) для всех поддоменов myserver-ai.ru.

## СТАТУС
🟡 Файлы готовы — ожидает деплоя на VPS

## ЧТО СДЕЛАНО
- [2026-04-15] Созданы все файлы: Homepage docker-compose, YAML конфиги (services, settings, widgets)
- [2026-04-15] Создан Authelia: docker-compose, configuration.yml (с плейсхолдерами секретов), users_database.yml
- [2026-04-15] Созданы nginx конфиги: homepage, authelia, vaultwarden (с auth), music (с auth), immich (с auth)
- [2026-04-15] Создан deploy.sh — полный скрипт деплоя с генерацией секретов и хэша пароля

## СЛЕДУЮЩИЙ ШАГ
1. Добавить DNS в Cloudflare: home.myserver-ai.ru → 147.45.238.120, auth.myserver-ai.ru → 147.45.238.120 (DNS only, без проксирования)
2. Запустить deploy.sh на VPS: `bash <(curl -sL https://raw.githubusercontent.com/nonamelogin1234/Claude_Home/main/HomePage/deploy.sh)`
3. Получить SSL через certbot: `certbot certonly --nginx -d home.myserver-ai.ru` и `certbot certonly --nginx -d auth.myserver-ai.ru`
4. Включить nginx конфиги и reload
5. Настроить TOTP на https://auth.myserver-ai.ru

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
