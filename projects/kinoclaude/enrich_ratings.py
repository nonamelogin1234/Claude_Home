#!/usr/bin/env python3
"""
Обогащение данных через KP API: жанры, рейтинги, описание, теги.
Обрабатывает до 450 фильмов за запуск (оставляет запас).
Запускается на VPS: python3 /opt/kinoclaude/enrich_ratings.py [--limit N]
"""
import sys
import time
import requests
import psycopg2

DB_DSN = "host=172.18.0.4 dbname=jarvis_memory user=jarvis password=jarvis_pass"
API_TOKEN = "33455aff-64f4-4f82-849e-e98473c46ce8"
KP_BASE = "https://kinopoiskapiunofficial.tech/api"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--limit" else 450


def kp_get(path, params=None):
    headers = {"X-API-KEY": API_TOKEN, "Content-Type": "application/json"}
    r = requests.get(f"{KP_BASE}{path}", headers=headers, params=params, timeout=10)
    if r.status_code == 429:
        print("  Лимит API! Останавливаюсь.")
        sys.exit(1)
    r.raise_for_status()
    return r.json()


def assign_tags(genres: list, year: int, kp_type: str) -> list:
    tags = []
    g = set(x.lower() for x in genres)

    # Жанровые теги
    genre_map = {
        "триллер": "триллер", "ужасы": "хоррор", "драма": "драма",
        "комедия": "комедия", "фантастика": "sci-fi", "криминал": "криминал",
        "боевик": "боевик", "мультфильм": "анимация", "аниме": "аниме",
        "документальный": "документальный", "биография": "байопик",
        "история": "историческое", "мелодрама": "мелодрама",
        "фэнтези": "фэнтези", "приключения": "приключения",
        "спорт": "спорт", "мюзикл": "мюзикл", "вестерн": "вестерн",
    }
    for kp_genre, tag in genre_map.items():
        if kp_genre in g:
            tags.append(tag)

    # Временная эпоха
    if year:
        if year < 1970:
            tags.append("классика")
        elif year < 1980:
            tags.append("70е")
        elif year < 1990:
            tags.append("80е")
        elif year < 2000:
            tags.append("90е")
        elif year < 2010:
            tags.append("2000е")
        elif year < 2020:
            tags.append("2010е")
        else:
            tags.append("новинка")

    # Формат
    if kp_type == "series":
        tags.append("сериал")

    return tags


def enrich():
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT film_id, kp_type, year FROM kinoclaude_ratings
        WHERE enriched_at IS NULL
        ORDER BY date_watched DESC
        LIMIT %s
    """, (LIMIT,))
    rows = cur.fetchall()
    print(f"Обогащаю {len(rows)} записей...")

    ok = 0
    for i, (film_id, kp_type, year) in enumerate(rows):
        try:
            data = kp_get(f"/v2.2/films/{film_id}")
            genres_list = [g["genre"] for g in data.get("genres", [])]
            tags = assign_tags(genres_list, year or data.get("year"), kp_type)

            cur.execute("""
                UPDATE kinoclaude_ratings SET
                    genres = %s,
                    tags = %s,
                    year = COALESCE(year, %s),
                    kp_rating = %s,
                    imdb_rating = %s,
                    description = %s,
                    enriched_at = NOW()
                WHERE film_id = %s
            """, (
                genres_list,
                tags,
                data.get("year"),
                data.get("ratingKinopoisk"),
                data.get("ratingImdb"),
                (data.get("description") or "")[:500],
                film_id,
            ))
            conn.commit()
            ok += 1
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(rows)}...")
            time.sleep(0.3)  # ~3 req/sec, не перегружаем
        except Exception as e:
            print(f"  ОШИБКА {film_id}: {e}")
            conn.rollback()
            time.sleep(1)

    cur.close()
    conn.close()
    print(f"Обогащено: {ok}/{len(rows)}")


if __name__ == "__main__":
    enrich()
