# RPG Tracker of Sergey

Тёмный DnD-дашборд для чтения прогресса Сергея напрямую из PostgreSQL и отображения его как RPG-путешествия.

## Файлы

- `backend/` — FastAPI API, SQL-логика, расчёты и кэш.
- `frontend/` — HTML/CSS/Vanilla JS интерфейс с Chart.js.
- `docker-compose.yml` — запуск backend + nginx, без локального Postgres.
- `nginx.conf.template` — проксирование `/api`, CSP, rate limiting и раздача статики.

## Переменные окружения

Скопируй `.env.example` в `.env` и заполни пароль:

```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=jarvis_memory
DB_USER=jarvis
DB_PASSWORD=
API_KEY=change_me
HERO_NAME=Сергей
HERO_CLASS=Воин — Путь Трансформации
CACHE_TTL_SECONDS=300
CORS_ORIGINS=http://localhost:8088,https://mcp.myserver-ai.ru
APP_PORT=8088
EXTERNAL_POSTGRES_NETWORK=shared-postgres
```

## Команды деплоя

```bash
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f backend
docker compose restart backend nginx
```

## Адрес

По умолчанию дашборд будет доступен на `http://<server>:8088/`.

## Заметки

- Имя внешней docker-сети вынесено в `EXTERNAL_POSTGRES_NETWORK`.
- `API_KEY` обязателен для production: nginx автоматически подставляет его в запросы к backend.
- Если в `hevy_sets` упражнение жима ног называется по-другому, скорректируй фильтр `LIKE '%жим ног%'` в `backend/db.py`.
