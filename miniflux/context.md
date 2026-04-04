# MINIFLUX + ДАЙДЖЕСТ В TELEGRAM

## ЦЕЛЬ
RSS-ридер Miniflux на VPS + автоматический утренний дайджест через Claude в Telegram.

## СТАТУС
🟡 Почти готов — нужно: заполнить 2 credentials в n8n + добавить RSS-ленты

## ЧТО СДЕЛАНО
- [2026-04-04] Создана БД `miniflux` в PostgreSQL (user: jarvis) → успешно
- [2026-04-04] Miniflux запущен в Docker на root_default сети, порт 127.0.0.1:8090 → работает
- [2026-04-04] Добавлена DNS A-запись rss→147.45.238.120 (серое облако Cloudflare)
- [2026-04-04] SSL-сертификат получен через `snap run certbot --nginx` → HTTPS работает
- [2026-04-04] nginx настроен: https://rss.myserver-ai.ru → 200 OK, вход работает
- [2026-04-04] n8n workflow создан (ID: LMmYunRuuGBTCnFO) → Miniflux Basic Auth встроен

## СЛЕДУЮЩИЙ ШАГ
1. В n8n workflow `LMmYunRuuGBTCnFO` заполнить:
   - Нода "Claude: составить дайджест" → параметр `x-api-key` → вставить Anthropic API key
   - Нода "Telegram: отправить дайджест" → добавить Telegram Bot credential + вставить TELEGRAM_CHAT_ID
2. Активировать workflow в n8n
3. Зайти в https://rss.myserver-ai.ru и добавить RSS-ленты

## ГРАБЛИ
- n8n → Miniflux: использовать `http://miniflux:8080` (оба в root_default сети), НЕ 127.0.0.1:8090
- Miniflux auth в n8n: Basic Auth заголовок `Basic YWRtaW46bWluaWZsdXgyMDI2IQ==` (admin:miniflux2026!)
- DNS rss.myserver-ai.ru: нужна A-запись, иначе certbot падает с NXDOMAIN
- certbot системный сломан (josepy/OpenSSL конфликт) → использовать `snap run certbot`

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Miniflux
- Контейнер: `miniflux`, образ `miniflux/miniflux:latest`
- Сеть: root_default (та же что n8n и postgres)
- Порт на хосте: 127.0.0.1:8090 → внутри контейнера :8080
- URL для n8n (изнутри Docker): http://miniflux:8080
- URL для браузера: https://rss.myserver-ai.ru (после DNS+SSL)
- Admin: admin / miniflux2026!
- БД: postgres://jarvis:jarvis_pass@172.18.0.4/miniflux?sslmode=disable
- Docker Compose: /srv/miniflux/docker-compose.yml

### n8n Workflow
- ID: LMmYunRuuGBTCnFO
- Название: "Miniflux Дайджест → Telegram (утро)"
- Триггер: каждый день 05:00 UTC (08:00 МСК)
- Claude модель: claude-haiku-4-5-20251001 (быстрая и дешёвая)
- Логика: GET /v1/entries?status=unread&limit=20 → Claude → Telegram → PUT mark as read
