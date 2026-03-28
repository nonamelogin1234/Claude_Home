#!/usr/bin/env python3
"""
KinoClaude MCP Server — SSE mode
Runs on port 8766, proxied via nginx
"""

import os
import json
import requests
import psycopg2
import psycopg2.extras
from fastmcp import FastMCP

API_TOKEN = os.environ.get("KINOPOISK_TOKEN", "")
BASE_URL = "https://kinopoiskapiunofficial.tech/api"
DB_DSN = "host=172.18.0.4 dbname=jarvis_memory user=jarvis password=jarvis_pass"
PROFILE_PATH = "/opt/kinoclaude/profile.md"

mcp = FastMCP("KinoClaude")


def _get(path: str, params: dict = None) -> dict:
    headers = {"X-API-KEY": API_TOKEN, "Content-Type": "application/json"}
    r = requests.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def _db():
    return psycopg2.connect(DB_DSN)


# ─── Кинопоиск API инструменты ───────────────────────────────────────────────

@mcp.tool()
def search_films(keyword: str, page: int = 1) -> str:
    """
    Поиск фильмов и сериалов по названию на Кинопоиске.
    Используй для поиска конкретного фильма или добавления оценки.
    Возвращает: ID | Название (год) | рейтинг | тип
    """
    data = _get("/v2.1/films/search-by-keyword", {"keyword": keyword, "page": page})
    films = data.get("films", [])
    if not films:
        return "Ничего не найдено"
    result = []
    for f in films[:10]:
        line = f"{f.get('filmId')} | {f.get('nameRu') or f.get('nameEn')} ({f.get('year', '?')}) | рейтинг: {f.get('rating', '?')} | {f.get('type', '?')}"
        result.append(line)
    return "\n".join(result)


@mcp.tool()
def get_film(film_id: int) -> str:
    """
    Получить подробную информацию о фильме по его ID с Кинопоиска.
    Возвращает название, год, жанры, рейтинг, описание, длительность.
    """
    data = _get(f"/v2.2/films/{film_id}")
    genres = ", ".join(g["genre"] for g in data.get("genres", []))
    countries = ", ".join(c["country"] for c in data.get("countries", []))
    return (
        f"ID: {data.get('kinopoiskId')}\n"
        f"Название: {data.get('nameRu') or data.get('nameEn')}\n"
        f"Год: {data.get('year')}\n"
        f"Жанры: {genres}\n"
        f"Страна: {countries}\n"
        f"Рейтинг КП: {data.get('ratingKinopoisk')}\n"
        f"Рейтинг IMDb: {data.get('ratingImdb')}\n"
        f"Длительность: {data.get('filmLength')} мин\n"
        f"Описание: {(data.get('description') or '')[:400]}"
    )


@mcp.tool()
def get_top_films(list_type: str = "TOP_250_BEST_FILMS", page: int = 1) -> str:
    """
    Получить топ фильмов с Кинопоиска.
    list_type: TOP_250_BEST_FILMS (топ-250) или TOP_100_POPULAR_FILMS (популярные сейчас)
    """
    data = _get("/v2.2/films/top", {"type": list_type, "page": page})
    films = data.get("films", [])
    if not films:
        return "Пусто"
    result = []
    for i, f in enumerate(films[:20], start=(page - 1) * 20 + 1):
        line = f"{i}. [{f.get('filmId')}] {f.get('nameRu') or f.get('nameEn')} ({f.get('year')}) | {f.get('rating')}"
        result.append(line)
    return "\n".join(result)


@mcp.tool()
def get_films_by_filters(
    genres: str = None,
    countries: str = None,
    year_from: int = None,
    year_to: int = None,
    rating_from: float = None,
    order: str = "RATING",
    film_type: str = "FILM",
    page: int = 1
) -> str:
    """
    Поиск фильмов по фильтрам — главный инструмент для рекомендаций.
    genres: ID жанра (1=боевик, 2=приключения, 4=фантастика, 6=мультфильм,
            13=ужасы, 14=криминал, 22=триллер, 24=драма, 40=комедия,
            55=история, 25=документальный, 26=мюзикл, 33=биография)
    countries: ID страны (1=США, 3=Франция, 6=Великобритания, 34=Италия,
               33=Германия, 43=СССР, 123=Россия)
    year_from / year_to: диапазон годов
    rating_from: минимальный рейтинг (например 7.0)
    order: RATING, NUM_VOTE, YEAR
    film_type: FILM, TV_SHOW, TV_SERIES, MINI_SERIES, ALL
    """
    params = {"order": order, "type": film_type, "page": page, "ratingFrom": 0, "ratingTo": 10}
    if genres:
        params["genres"] = genres
    if countries:
        params["countries"] = countries
    if year_from:
        params["yearFrom"] = year_from
    if year_to:
        params["yearTo"] = year_to
    if rating_from:
        params["ratingFrom"] = rating_from

    data = _get("/v2.2/films", params)
    films = data.get("items", [])
    total = data.get("total", 0)
    if not films:
        return "Ничего не найдено по заданным фильтрам"
    result = [f"Найдено: {total}, показываю страницу {page}:"]
    for f in films:
        genres_str = ", ".join(g["genre"] for g in f.get("genres", []))
        line = f"[{f.get('kinopoiskId')}] {f.get('nameRu') or f.get('nameEn')} ({f.get('year')}) | {f.get('ratingKinopoisk')} | {genres_str}"
        result.append(line)
    return "\n".join(result)


@mcp.tool()
def get_film_staff(film_id: int) -> str:
    """
    Получить режиссёра и актёров фильма по его ID.
    """
    data = _get("/v1/staff", {"filmId": film_id})
    if not data:
        return "Данные недоступны"
    director = next((p for p in data if p.get("professionKey") == "DIRECTOR"), None)
    actors = [p for p in data if p.get("professionKey") == "ACTOR"][:10]
    result = []
    if director:
        result.append(f"Режиссёр: {director.get('nameRu') or director.get('nameEn')}")
    if actors:
        names = ", ".join(a.get('nameRu') or a.get('nameEn', '?') for a in actors)
        result.append(f"Актёры: {names}")
    return "\n".join(result) if result else "Нет данных"


# ─── Личная база просмотров ───────────────────────────────────────────────────

@mcp.tool()
def get_my_ratings(status: str = None, genres: str = None, tags: str = None, limit: int = 50) -> str:
    """
    Выборка из личной базы просмотренных фильмов с фильтрами.
    Это ГЛАВНЫЙ инструмент для исключения уже просмотренного из рекомендаций.

    status: 'watched' (просмотрено), 'want' (хочу посмотреть) — по умолчанию все
    genres: фильтр по жанру (подстрока, например 'триллер')
    tags: фильтр по тегу (подстрока, например 'sci-fi')
    limit: сколько записей вернуть (макс 200)

    Возвращает: film_id | title | year | genres | tags | date_watched
    Используй чтобы: 1) получить список уже просмотренных ID для исключения
                     2) найти похожие фильмы которые понравились
    """
    conn = _db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT film_id, kp_type, title, title_ru, year, genres, tags, my_rating, status, date_watched FROM kinoclaude_ratings WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if genres:
        query += " AND genres::text ILIKE %s"
        params.append(f"%{genres}%")
    if tags:
        query += " AND tags::text ILIKE %s"
        params.append(f"%{tags}%")
    query += " ORDER BY date_watched DESC NULLS LAST LIMIT %s"
    params.append(min(limit, 200))

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return "Ничего не найдено"
    result = [f"Найдено: {len(rows)} записей:"]
    for r in rows:
        title = r['title'] or r['title_ru'] or '?'
        genres_str = ", ".join(r['genres']) if r['genres'] else "—"
        tags_str = ", ".join(r['tags']) if r['tags'] else "—"
        rating_str = str(r['my_rating']) if r['my_rating'] else "—"
        date_str = str(r['date_watched']) if r['date_watched'] else "—"
        line = f"{r['film_id']} | {title} ({r['year'] or '?'}) | жанры: {genres_str} | теги: {tags_str} | оценка: {rating_str} | {date_str}"
        result.append(line)
    return "\n".join(result)


@mcp.tool()
def rate_film(film_id: int, title: str, rating: float = None, status: str = "watched") -> str:
    """
    Сохранить или обновить оценку фильма в личной базе.
    film_id: ID фильма на Кинопоиске
    title: название (английское или русское)
    rating: оценка от 1 до 10 (необязательно)
    status: 'watched' (просмотрено) или 'want' (хочу посмотреть)
    """
    conn = _db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO kinoclaude_ratings (film_id, title, my_rating, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (film_id) DO UPDATE SET
            my_rating = EXCLUDED.my_rating,
            status = EXCLUDED.status,
            title = COALESCE(EXCLUDED.title, kinoclaude_ratings.title)
    """, (film_id, title, rating, status))
    conn.commit()
    cur.close()
    conn.close()
    rating_str = f" с оценкой {rating}" if rating else ""
    return f"✓ Сохранено: [{film_id}] {title} — {status}{rating_str}"


@mcp.tool()
def get_profile() -> str:
    """
    Вернуть профиль вкусов киномана.
    Читай ВСЕГДА в начале сценария «Посоветуй фильм».
    Содержит: любимые жанры, режиссёры, паттерны вкуса, что не заходит.
    """
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Профиль не найден. Запусти генерацию профиля."


@mcp.tool()
def add_to_blacklist(film_id: int, title: str, reason: str = None) -> str:
    """
    Добавить фильм в чёрный список — «никогда не смотреть».
    film_id: ID фильма на Кинопоиске
    title: название фильма
    reason: причина (необязательно)
    """
    conn = _db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO kinoclaude_blacklist (film_id, title, reason)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (film_id, title, reason))
    conn.commit()
    cur.close()
    conn.close()
    return f"✓ [{film_id}] {title} добавлен в чёрный список"


@mcp.tool()
def get_blacklist() -> str:
    """
    Получить список фильмов из чёрного списка.
    Используй при рекомендациях чтобы исключить нежелательные фильмы.
    """
    conn = _db()
    cur = conn.cursor()
    cur.execute("SELECT film_id, title, reason, added_at FROM kinoclaude_blacklist ORDER BY added_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return "Чёрный список пуст"
    result = [f"Чёрный список ({len(rows)} записей):"]
    for film_id, title, reason, added_at in rows:
        reason_str = f" — {reason}" if reason else ""
        result.append(f"{film_id} | {title}{reason_str}")
    return "\n".join(result)


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8766)
