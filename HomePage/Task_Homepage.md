# Task: Homepage + Authelia — централизованный доступ к сервисам

## Контекст
Ты знаком с инфраструктурой. Коротко: VPS `147.45.238.120` (myserver-ai.ru, Ubuntu 24.04),
домашний сервер `10.8.0.27` (через WireGuard wg1), все сервисы за nginx, Docker.
Домашний сервер доступен только через WireGuard — напрямую из интернета не открыт.

Цель этой задачи: поднять красивую стартовую страницу со всеми сервисами
и закрыть её (и все поддомены) единой аутентификацией через Authelia.

---

## Часть 1 — Homepage (стартовая страница)

### Что это
Homepage (https://gethomepage.dev) — self-hosted dashboard с карточками сервисов,
виджетами живых данных, настройкой через YAML. Запускается в Docker на VPS.

### Где разместить
- Docker-контейнер на VPS
- Поддомен: `home.myserver-ai.ru`
- Порт контейнера: 3000 (внутренний)
- nginx reverse proxy на VPS (новый конфиг в /etc/nginx/sites-available/homepage)
- SSL: через acme.sh (уже настроен на VPS, использовать тот же pipeline)

### Docker — добавить в существующую инфраструктуру
Создать `/opt/homepage/docker-compose.yml`:

```yaml
services:
  homepage:
    image: ghcr.io/gethomepage/homepage:latest
    container_name: homepage
    ports:
      - "3000:3000"
    volumes:
      - /opt/homepage/config:/app/config
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
```


### Конфигурация Homepage (/opt/homepage/config/)

**services.yaml** — все сервисы разбить по группам:

```yaml
- Основное:
    - n8n:
        href: https://myserver-ai.ru
        description: Автоматизация
        icon: n8n.png
        widget:
          type: n8n
          url: http://172.18.0.1:5678
    - Vaultwarden:
        href: https://vault.myserver-ai.ru
        description: Пароли
        icon: bitwarden.png

- Медиа (домашний сервер):
    - Jellyfin:
        href: http://192.168.0.103:8096
        description: Фильмы
        icon: jellyfin.png
    - Navidrome:
        href: https://music.myserver-ai.ru
        description: Музыка
        icon: navidrome.png
    - Immich:
        href: https://photos.myserver-ai.ru
        description: Фото
        icon: immich.png

- Данные:
    - Nextcloud:
        href: https://nextcloud.myserver-ai.ru
        description: Файлы
        icon: nextcloud.png
    - Codex RPG:
        href: https://rpg.myserver-ai.ru
        description: Трекер здоровья
        icon: si-databricks

- Инструменты:
    - qBittorrent:
        href: http://192.168.0.103:8080
        description: Торренты
        icon: qbittorrent.png
    - Miniflux:
        href: https://rss.myserver-ai.ru
        description: RSS
        icon: miniflux.png
```

**settings.yaml**:
```yaml
title: myserver-ai
theme: dark
color: slate
headerStyle: boxed
language: ru
```

**widgets.yaml** — виджеты вверху страницы:
```yaml
- datetime:
    text_size: xl
    format:
      dateStyle: long
      timeStyle: short
      hourCycle: h23
- greeting:
    text_size: xl
    text: Добро пожаловать
```


### nginx конфиг для Homepage

Файл `/etc/nginx/sites-available/homepage`:
```nginx
server {
    listen 443 ssl;
    server_name home.myserver-ai.ru;

    ssl_certificate /etc/nginx/ssl/home.myserver-ai.ru.crt;
    ssl_certificate_key /etc/nginx/ssl/home.myserver-ai.ru.key;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name home.myserver-ai.ru;
    return 301 https://$host$request_uri;
}
```

SSL получить через acme.sh (аналогично другим поддоменам):
```bash
~/.acme.sh/acme.sh --issue --nginx -d home.myserver-ai.ru
~/.acme.sh/acme.sh --install-cert -d home.myserver-ai.ru \
  --cert-file /etc/nginx/ssl/home.myserver-ai.ru.crt \
  --key-file /etc/nginx/ssl/home.myserver-ai.ru.key \
  --reloadcmd "systemctl reload nginx"
```

DNS: добавить A-запись `home` → `147.45.238.120` в Cloudflare (DNS only, без проксирования).

---

## Часть 2 — Authelia (единая аутентификация)

### Что это
Authelia — SSO/2FA прокси. Встаёт перед nginx и требует логин + TOTP
для доступа ко всем защищённым поддоменам. Вошёл один раз — везде открыто.

### Архитектура
```
браузер → nginx → Authelia (проверка сессии)
                     ↓ если не авторизован → форма логина Authelia
                     ↓ если авторизован → пропускает на сервис
```

### Где поднять
- Docker-контейнер на VPS рядом с остальными
- Внутренний порт: 9091
- Поддомен для формы входа: `auth.myserver-ai.ru`


### Docker — Authelia

Добавить в `/opt/authelia/docker-compose.yml`:

```yaml
services:
  authelia:
    image: authelia/authelia:latest
    container_name: authelia
    volumes:
      - /opt/authelia/config:/config
    ports:
      - "9091:9091"
    restart: unless-stopped
    environment:
      - TZ=Europe/Moscow
```

### Конфиг Authelia (/opt/authelia/config/configuration.yml)

Ключевые параметры:

```yaml
server:
  host: 0.0.0.0
  port: 9091

log:
  level: info

jwt_secret: <сгенерировать: openssl rand -hex 32>
default_redirection_url: https://home.myserver-ai.ru

authentication_backend:
  file:
    path: /config/users_database.yml

session:
  secret: <сгенерировать: openssl rand -hex 32>
  domain: myserver-ai.ru   # важно: общий домен для всех поддоменов
  expiration: 12h
  inactivity: 2h

storage:
  local:
    path: /config/db.sqlite3

notifier:
  filesystem:
    filename: /config/notification.txt  # без email, просто файл

access_control:
  default_policy: deny
  rules:
    - domain: "home.myserver-ai.ru"
      policy: two_factor
    - domain: "vault.myserver-ai.ru"
      policy: two_factor
    - domain: "photos.myserver-ai.ru"
      policy: two_factor
    - domain: "nextcloud.myserver-ai.ru"
      policy: bypass   # у Nextcloud своя авторизация, не дублировать
    - domain: "myserver-ai.ru"
      policy: two_factor
    - domain: "music.myserver-ai.ru"
      policy: two_factor
    - domain: "rss.myserver-ai.ru"
      policy: two_factor
    - domain: "auth.myserver-ai.ru"
      policy: bypass
```

### Пользователь (/opt/authelia/config/users_database.yml)

Сгенерировать хэш пароля: `docker run authelia/authelia:latest authelia hash-password 'ВАШ_ПАРОЛЬ'`

```yaml
users:
  sergei:
    displayname: Sergei
    password: "$argon2id$..."   # вставить хэш
    email: nonamepogin@gmail.com
    groups:
      - admins
```


### nginx — интеграция Authelia

В каждый защищённый server-блок добавить:

```nginx
# Внутри location / каждого защищённого сервиса:
auth_request /authelia;
auth_request_set $target_url $scheme://$http_host$request_uri;
error_page 401 =302 https://auth.myserver-ai.ru/?rd=$target_url;

location /authelia {
    internal;
    proxy_pass http://127.0.0.1:9091/api/verify;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URL $scheme://$http_host$request_uri;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Отдельный server-блок для `auth.myserver-ai.ru`:
```nginx
server {
    listen 443 ssl;
    server_name auth.myserver-ai.ru;

    ssl_certificate /etc/nginx/ssl/auth.myserver-ai.ru.crt;
    ssl_certificate_key /etc/nginx/ssl/auth.myserver-ai.ru.key;

    location / {
        proxy_pass http://127.0.0.1:9091;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

SSL для `auth.myserver-ai.ru` — получить через acme.sh аналогично.
DNS: A-запись `auth` → `147.45.238.120` в Cloudflare.

---

## Часть 3 — Порядок выполнения

1. **Создать DNS-записи** в Cloudflare:
   - `home.myserver-ai.ru` → 147.45.238.120 (DNS only)
   - `auth.myserver-ai.ru` → 147.45.238.120 (DNS only)

2. **Поднять Homepage**:
   - Создать `/opt/homepage/`, написать docker-compose.yml и конфиги
   - `docker compose up -d`
   - Получить SSL через acme.sh
   - Прописать nginx конфиг, `nginx -t && systemctl reload nginx`
   - Проверить: https://home.myserver-ai.ru открывается без авторизации

3. **Поднять Authelia**:
   - Создать `/opt/authelia/config/`
   - Написать configuration.yml (с реальными секретами через openssl)
   - Создать users_database.yml с хэшем пароля
   - `docker compose up -d`
   - Прописать nginx конфиг для auth.myserver-ai.ru
   - Проверить: https://auth.myserver-ai.ru открывает форму входа

4. **Подключить Authelia к сервисам**:
   - Добавить `auth_request` блоки в nginx конфиги существующих сервисов
   - Начать с homepage, проверить что редирект на auth работает
   - После успешной проверки — добавить в остальные поддомены
   - `nginx -t && systemctl reload nginx` после каждого изменения

5. **Настроить TOTP**:
   - Войти на https://auth.myserver-ai.ru
   - Зарегистрировать TOTP в любом приложении (Google Authenticator / Aegis)
   - Проверить полный flow: анонимный → редирект на auth → логин + TOTP → доступ


---

## Часть 4 — Грабли и важные детали

- **Nextcloud и Authelia**: не защищать Nextcloud через Authelia — у него своя авторизация,
  двойной слой сломает WebDAV и мобильные клиенты. В access_control ставить `policy: bypass`.

- **n8n webhooks**: если есть активные webhook-эндпоинты в n8n (Finance Фёдор и др.),
  они должны оставаться доступными без Authelia. Добавить исключение:
  ```yaml
  - domain: myserver-ai.ru
    resources:
      - "^/webhook/.*$"
    policy: bypass
  ```

- **session.domain**: обязательно `myserver-ai.ru` (без поддомена) — это позволяет
  использовать одну сессию для всех поддоменов.

- **Секреты**: jwt_secret и session secret генерировать через `openssl rand -hex 32`,
  не хардкодить в конфиге как есть — использовать реальные значения.

- **Порядок nginx**: блок `location /authelia` должен быть внутри каждого server-блока,
  не снаружи. Иначе nginx не найдёт internal location.

- **KinoClaude MCP**: порт 8767 — это MCP-сервер для Claude Desktop, не трогать,
  не закрывать Authelia. Он уже защищён отдельно (nginx + нет публичного поддомена).

- **Shell API**: порт 7723/7724 — не трогать, не закрывать Authelia.

---

## Итог — что должно работать после задачи

- `https://home.myserver-ai.ru` — стартовая страница со всеми сервисами
- `https://auth.myserver-ai.ru` — форма входа Authelia
- Любой незалогиненный запрос на защищённый поддомен → редирект на auth
- Один логин + TOTP → доступ ко всем сервисам на 12 часов
- Nextcloud, n8n webhooks — работают без Authelia (bypass)
- Homepage показывает живые данные (uptime контейнеров через Docker socket)
