#!/usr/bin/env python3
"""
Загрузка истории просмотров из kinoclaude_ratings.md в PostgreSQL.
Запускается на VPS: python3 /opt/kinoclaude/load_ratings.py
"""
import re
import sys
import requests
import psycopg2
from datetime import datetime

RAW_URL = "https://raw.githubusercontent.com/nonamelogin1234/Claude_Home/main/kinoclaude/kinoclaude_ratings.md"
DB_DSN = "host=172.18.0.4 dbname=jarvis_memory user=jarvis password=jarvis_pass"
API_TOKEN = "33455aff-64f4-4f82-849e-e98473c46ce8"
KP_BASE = "https://kinopoiskapiunofficial.tech/api"


def parse_year(title_ru: str) -> int | None:
    m = re.search(r'\((\d{4})\)', title_ru)
    return int(m.group(1)) if m else None


def parse_date(date_str: str):
    """'13.03.2026, 18:03' -> date"""
    try:
        return datetime.strptime(date_str.strip().split(",")[0], "%d.%m.%Y").date()
    except Exception:
        return None


def load_file():
    print("Скачиваю файл с GitHub...")
    r = requests.get(RAW_URL, timeout=30)
    r.raise_for_status()
    content = r.content.decode("utf-16")
    lines = content.strip().splitlines()
    print(f"Строк: {len(lines)}")

    records = []
    for line in lines:
        cols = line.strip().split("\t")
        if len(cols) < 4:
            continue
        url = cols[1].strip()
        # Чистим артефакты из url типа '" style="color: #999'
        url = re.sub(r'".*', '', url).strip()
        m = re.match(r'/(film|series)/(\d+)/', url)
        if not m:
            continue
        kp_type = m.group(1)
        film_id = int(m.group(2))
        title_ru = cols[2].strip()
        title_en = cols[3].strip()
        # Убираем &nbsp; и HTML-сущности
        if title_en in ("&nbsp;", "", " "):
            title_en = None
        date_str = cols[4].strip() if len(cols) > 4 else ""
        year = parse_year(title_ru)
        date_watched = parse_date(date_str)

        records.append({
            "film_id": film_id,
            "kp_type": kp_type,
            "title": title_en,
            "title_ru": title_ru,
            "year": year,
            "date_watched": date_watched,
        })

    return records


def insert_records(records):
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    for r in records:
        try:
            cur.execute("""
                INSERT INTO kinoclaude_ratings
                    (film_id, kp_type, title, title_ru, year, status, date_watched)
                VALUES (%s, %s, %s, %s, %s, 'watched', %s)
                ON CONFLICT (film_id) DO NOTHING
            """, (r["film_id"], r["kp_type"], r["title"], r["title_ru"],
                  r["year"], r["date_watched"]))
            if cur.rowcount:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ОШИБКА {r['film_id']}: {e}")
            conn.rollback()
            continue
    conn.commit()
    cur.close()
    conn.close()
    print(f"Вставлено: {inserted}, пропущено (уже есть): {skipped}")


if __name__ == "__main__":
    records = load_file()
    insert_records(records)
    print("Готово!")
