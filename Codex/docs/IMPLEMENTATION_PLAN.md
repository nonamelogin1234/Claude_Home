# Технический план RPG-трекера

## Структура проекта

```text
/opt/rpg-tracker/
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── repository.py
│   ├── progress.py
│   ├── config.py
│   ├── security.py
│   ├── models.py
│   ├── cache.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/
│   └── IMPLEMENTATION_PLAN.md
├── docker-compose.yml
├── nginx.conf.template
└── README.md
```

## Алгоритмы

### Карточка героя

1. Получить количество тренировок из `hevy_workouts`.
2. Сопоставить число тренировок с порогами уровней: `1-10`, `11-25`, `26-50`, `51-100`, `100+`.
3. Рассчитать прогресс внутри текущего диапазона.
4. Сила: взять последнюю тренировку и максимальный `weight_kg` по упражнениям с названием, содержащим `жим ног`.
5. Выносливость: средние шаги за 7 дней разделить на 100.
6. Восстановление: средний `deep_sleep_min` за 7 дней.
7. Объём: сумма `total_volume_kg` за 30 дней.

### Квесты

1. Серия недель: получить уникальные `DATE_TRUNC('week', workout_date)` и посчитать подряд идущие недели.
2. Пауза между тренировками: взять последние даты тренировок и найти максимальный разрыв в днях.
3. Серия сна: пройти по последним дням из `health_daily_summary`, пока `deep_sleep_min > 120`.
4. Покоритель объёма: сравнить объём текущей недели с лучшим предыдущим недельным объёмом.
5. Архивные квесты: определять по общему числу тренировок.

### Боссы

1. Взять текущий вес и максимальный исторический вес.
2. Если текущий вес уже ниже цели босса, статус `completed`.
3. Первый ещё не побеждённый босс становится `active`.
4. Следующие боссы получают статус `locked`.
5. Прогресс вычисляется как доля пути от стартового веса к цели.

### Лог событий

1. Собрать тренировки, замеры веса, глубокий сон и рекорды отдельными запросами.
2. Для тренировок считать процент к предыдущей через `LAG`.
3. Для рекордов искать сеты, где `weight_kg` больше предыдущего максимума по упражнению.
4. Слить данные в единый список, отсортировать по дате, взять 15 записей.

## SQL-запросы

### `/api/hero`

```sql
WITH latest_workout AS (
    SELECT MAX(workout_date::date) AS workout_date
    FROM hevy_workouts
),
latest_leg_press AS (
    SELECT MAX(weight_kg) AS max_leg_press
    FROM hevy_sets
    WHERE workout_date::date = (SELECT workout_date FROM latest_workout)
      AND LOWER(exercise_title) LIKE '%жим ног%'
),
endurance AS (
    SELECT AVG(COALESCE(steps, 0)) AS avg_steps
    FROM health_daily_summary
    WHERE date >= CURRENT_DATE - INTERVAL '6 days'
),
recovery AS (
    SELECT AVG(COALESCE(deep_sleep_min, 0)) AS avg_deep_sleep
    FROM health_daily_summary
    WHERE date >= CURRENT_DATE - INTERVAL '6 days'
),
monthly_volume AS (
    SELECT SUM(COALESCE(total_volume_kg, 0)) AS total_volume_kg
    FROM hevy_workouts
    WHERE workout_date::date >= CURRENT_DATE - INTERVAL '29 days'
)
SELECT
    COALESCE((SELECT COUNT(*) FROM hevy_workouts), 0) AS total_workouts,
    (SELECT workout_date FROM latest_workout) AS last_workout_date,
    COALESCE((SELECT max_leg_press FROM latest_leg_press), 0) AS strength_value,
    COALESCE((SELECT avg_steps FROM endurance), 0) / 100.0 AS endurance_value,
    COALESCE((SELECT avg_deep_sleep FROM recovery), 0) AS recovery_value,
    COALESCE((SELECT total_volume_kg FROM monthly_volume), 0) AS volume_value;
```

### `/api/stats`

```sql
WITH latest_weight AS (
    SELECT measured_at::date AS measured_date, weight
    FROM body_measurements
    ORDER BY measured_at DESC
    LIMIT 1
),
record_workout AS (
    SELECT workout_date::date AS workout_date, total_volume_kg
    FROM hevy_workouts
    ORDER BY total_volume_kg DESC NULLS LAST, workout_date DESC
    LIMIT 1
),
recent_five AS (
    SELECT AVG(COALESCE(total_volume_kg, 0)) AS avg_volume
    FROM (
        SELECT total_volume_kg
        FROM hevy_workouts
        ORDER BY workout_date DESC
        LIMIT 5
    ) t
)
SELECT
    (SELECT weight FROM latest_weight) AS current_weight,
    (SELECT measured_date FROM latest_weight) AS current_weight_date,
    COALESCE((SELECT COUNT(*) FROM hevy_workouts), 0) AS total_workouts,
    COALESCE((
        SELECT COUNT(*)
        FROM hevy_workouts
        WHERE workout_date::date >= CURRENT_DATE - INTERVAL '29 days'
    ), 0) AS workouts_last_30_days,
    COALESCE((SELECT SUM(COALESCE(total_volume_kg, 0)) FROM hevy_workouts), 0) AS total_volume_kg,
    (SELECT workout_date FROM record_workout) AS record_workout_date,
    COALESCE((SELECT total_volume_kg FROM record_workout), 0) AS record_workout_volume_kg,
    COALESCE((SELECT avg_volume FROM recent_five), 0) AS average_last_5_workouts_kg;
```

### `/api/events` и квесты

Запросы для событий, weekly progress и boss progress вынесены в `backend/repository.py` и реализованы с `COALESCE`, `LAG`, оконными агрегатами и fallback-обработкой для пустых таблиц.

## Полировка плана

- Пустые таблицы не ломают API: все критичные поля проходят через `COALESCE`.
- При падении PostgreSQL API возвращает stale cache или fallback JSON.
- Для docker compose используется внешняя сеть и отдельный nginx template, без локального Postgres.
- Фронтенду достаточно шести эндпоинтов: дополнительных ручек не требуется.

## Деплой

1. Скопировать проект в `/opt/rpg-tracker`.
2. Создать `.env` с `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
3. Проверить название общей docker-сети с контейнером `postgres`.
4. Выполнить `docker compose build`.
5. Выполнить `docker compose up -d`.
6. Проверить `docker compose ps` и `curl http://localhost/health`.

## Риски

- Если фактическое название упражнения отличается от шаблона `%жим ног%`, нужно поправить фильтр в SQL.
- Если имя внешней docker-сети на VPS другое, надо заменить его в `docker-compose.yml`.
- Если даты в БД лежат в другой timezone, стоит унифицировать timezone на стороне SQL.
