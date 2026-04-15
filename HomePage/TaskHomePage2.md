# ЗАДАНИЕ: Homepage — Полный редизайн и новые функции

**Дата:** 2026-04-15  
**Приоритет:** Визуальная красота — главный критерий. Функционал важен, но если что-то мешает красоте — жертвуем функционалом, не красотой.

---

## КОНТЕКСТ

Текущая инфраструктура:
- Homepage v1 работает на https://home.myserver-ai.ru (Docker, порт 3030, /opt/homepage/)
- Authelia на https://auth.myserver-ai.ru (Docker, порт 9091, /opt/authelia/)
- VPS: 147.45.238.120, Ubuntu 24.04
- Все сервисы — см. секцию «Сервисы» ниже

Сервисы на хоумпейдже:
- n8n → https://myserver-ai.ru
- Vaultwarden → https://vault.myserver-ai.ru
- Jellyfin → http://192.168.0.103:8096
- Navidrome → https://music.myserver-ai.ru
- Immich → https://photos.myserver-ai.ru
- Nextcloud → https://nextcloud.myserver-ai.ru
- Codex RPG → https://mcp.myserver-ai.ru:8769
- qBittorrent → http://192.168.0.103:8080

---

## ЗАДАЧА 1 — SSO: автологин при переходе с хоумпейджа

**Цель:** пользователь зашёл на home.myserver-ai.ru, прошёл Authelia один раз — и все клики по иконкам сервисов открываются без повторного ввода пароля/TOTP.

**Механика:** Authelia уже ставит cookie на домен `.myserver-ai.ru`. Значит сессия **уже есть** — просто надо убедиться, что nginx для каждого сервиса правильно проверяет её через `auth_request`.

**Что сделать:**
1. Проверить nginx-конфиги каждого сервиса: vault, photos, music, n8n, nextcloud.
2. Для каждого добавить/проверить блок `auth_request`:
```nginx
auth_request /authelia;
auth_request_set $target_url $scheme://$http_host$request_uri;
error_page 401 =302 https://auth.myserver-ai.ru/?rd=$target_url;

location = /authelia {
    internal;
    proxy_pass http://127.0.0.1:9091/api/authz/forward-auth;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $http_host;
    proxy_set_header X-Forwarded-URI $request_uri;
    proxy_set_header Content-Length "";
    proxy_pass_request_body off;
}
```
3. В Authelia `configuration.yml` — сессия уже настроена на `domain: myserver-ai.ru`, это правильно. Проверить что `expiration: 12h` и `inactivity: 2h` не слишком короткие — если надо, поставить `expiration: 168h` (неделя) и `inactivity: 24h`.
4. Для сервисов с мобильными клиентами (vault, music), где Authelia ломает API — оставить `policy: bypass` в access_control, но добавить `auth_request` только в браузерный location.

**Ожидаемый результат:** зашёл один раз с TOTP → неделю кликаешь по иконкам без единого запроса пароля.

---

## ЗАДАЧА 2 — Визуальный редизайн

**Приоритет: МАКСИМАЛЬНЫЙ.**

**Текущий стек:** gethomepage/homepage (YAML-конфиги, ограниченные темы).

**Оценить:** может ли стандартный Homepage дать действительно красивый результат с кастомным CSS/фоном/иконками — или нужно мигрировать.

### Вариант A: Остаёмся на Homepage, максимально прокачиваем

Homepage поддерживает:
- Кастомный CSS через `custom.css`
- Фоновое изображение (градиент или картинка)
- Кастомные иконки
- Цветовые темы

Если остаёмся — сделать:
1. Найти в интернете 3-5 топовых референсов красивых Homepage-дашбордов (r/selfhosted, HomeLab community). Реализовать лучший стиль.
2. Тёмная тема с glassmorphism-карточками сервисов (backdrop-filter: blur).
3. Фон — живой градиент или красивое статичное изображение (space/abstract/dark aesthetic).
4. Иконки — PNG высокого качества или SVG для всех сервисов.
5. Шрифт — Google Fonts (Inter или Geist).
6. Кастомный CSS файл `/opt/homepage/config/custom.css` с полным переопределением стилей карточек, хедера, фона.

### Вариант B: Миграция на Dashy (рекомендуется если A недостаточно)

Dashy (https://dashy.to) — значительно более гибкий в плане визуала:
- Темы, градиенты, glassmorphism из коробки
- Каждая карточка кастомизируется
- Поддержка кастомного CSS
- Статус-индикаторы сервисов

Если мигрируем:
1. Добавить контейнер `dashy` в docker-compose на порту 3031 (3030 занят Homepage).
2. Перенести все сервисы в `conf.yml` Dashy.
3. Настроить красивую тему — найти референсы и реализовать.
4. Nginx: переключить `home.myserver-ai.ru` с 3030 на 3031.
5. Старый Homepage не удалять — держать на 3030 как fallback до проверки.

**Критерии красоты (обязательно):**
- Glassmorphism или неоморфизм карточек
- Тёмный фон с акцентными цветами (глубокий синий / фиолетовый / изумрудный)
- Плавные hover-эффекты на иконках
- Статус-индикаторы (зелёный кружок = онлайн)
- Приятная типографика, не системный шрифт

---

## ЗАДАЧА 3 — Виджет новостей через Grok API

**Концепция:** кнопка «Сводка» на дашборде → запрос к Grok API → короткая яркая сводка по 3 темам → отображается прямо на странице.

### Реализация:

**Бэкенд** — новый Python-сервис `grok-news` на VPS:
- Файл: `/opt/grok-news/server.py`
- Порт: 8770
- Маршрут: `POST /summary` → обращается к Grok API (api.x.ai) с промптом
- Маршрут: `GET /health`
- Systemd-юнит: `grok-news.service`

**Промпт для Grok:**
```
Дай короткую яркую сводку (5-7 пунктов) самого важного за последние 24 часа по темам:
1. Мировая политика и геополитика
2. Мировые лидеры (решения, заявления, скандалы)
3. ИИ и технологии

Формат: по 2-3 пункта на тему. Каждый пункт — 1 предложение. Стиль: умный, прямой, без воды.
Отвечай на русском.
```

**API ключ Grok:**
- Взять из Vaultwarden: элемент с названием `Grok API Key` (или создать)
- На сервере хранить в `/opt/grok-news/.env` как `GROK_API_KEY=...`
- Claude Code должен спросить пользователя вставить ключ вручную в .env

**Nginx:** добавить location `/grok-news/` → `http://127.0.0.1:8770/`

**Фронтенд:**
- Если Homepage: через кастомный iframe на отдельную страницу `/grok-news/ui`
- Если Dashy: через кастомный iframe-виджет
- UI: кнопка «Обновить сводку» + блок с текстом + время последнего обновления + loader-анимация

---

## ЗАДАЧА 4 — Виджет погоды

**Источник:** OpenWeatherMap (бесплатный tier, ключ в Vaultwarden: `OpenWeatherMap API Key`)  
**Город:** Санкт-Петербург (lat=59.9386, lon=30.3141)

**Что отображать:**
- Текущая температура + иконка погоды
- Прогноз на 3 дня (мин/макс + иконка)
- Ощущаемая температура, влажность, ветер

**Реализация:**
- Homepage: использовать встроенный виджет `openweathermap` в `widgets.yaml`
- Dashy: виджет `weather` или кастомный через API

**Визуал:** минималистично, красиво, вписывается в общую тёмную тему. Иконки погоды — анимированные если возможно.

---

## ЗАДАЧА 5 — Виджет здоровья

**Концепция:** маленький блок «Путь к цели» — минималистичный, мотивирующий.

**Данные из PostgreSQL** (jarvis_memory на 172.18.0.4:5432, user: jarvis, pass: jarvis_pass):
- Последний вес: `SELECT value FROM body_measurements ORDER BY date DESC LIMIT 1`
- Цель: 85 кг
- Дней без курения: считать от 2025-02-13 до сегодня

**Бэкенд** — расширить `grok-news` сервис ИЛИ создать отдельный `health-widget`:
- Маршрут `GET /health-stats` → возвращает JSON: `{weight, goal, diff, smoke_days}`
- Подключение к PostgreSQL через psycopg2

**Фронтенд:**
- Текущий вес → стрелка → цель 85 кг
- Прогресс-бар (от стартового веса ~117 кг к цели 85 кг)
- «🚭 X дней без сигарет» — большой, яркий счётчик
- Стиль: glassmorphism-карточка, акцентный цвет (зелёный для прогресса)

---

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

```
VPS: 147.45.238.120
Shell: POST https://mcp.myserver-ai.ru:7723, X-Secret: shell-api-secret-2026
GitHub: github.com/nonamelogin1234/Claude_Home (ветка main)
Homepage config: /opt/homepage/config/
Authelia config: /opt/authelia/config/
Nginx sites: /etc/nginx/sites-available/ + sites-enabled/
PostgreSQL: 172.18.0.4:5432, db: jarvis_memory, user: jarvis, pass: jarvis_pass
```

## ПОРЯДОК ВЫПОЛНЕНИЯ

1. Сначала — редизайн (Задача 2). Определить Dashy vs Homepage, реализовать.
2. SSO (Задача 1) — проверить и починить nginx auth_request для всех сервисов.
3. Grok-сервис (Задача 3) — бэкенд + интеграция в дашборд.
4. Погода (Задача 4) — виджет.
5. Здоровье (Задача 5) — виджет.
6. Обновить `HomePage/context.md` и `brain/projects.md` в репо.

## РЕЗУЛЬТАТ

- https://home.myserver-ai.ru — красивый, сочный дашборд, референс-уровень r/selfhosted
- Один логин на всё, неделю без повторной аутентификации
- Сводка новостей по кнопке
- Погода СПб
- Счётчик дней без курения + прогресс к цели по весу
