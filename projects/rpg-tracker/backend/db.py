import os
import psycopg2
import psycopg2.extras
from typing import Optional, Any
import traceback

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "172.18.0.4"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "jarvis_memory"),
    "user": os.getenv("DB_USER", "jarvis"),
    "password": os.getenv("DB_PASSWORD", "jarvis_pass"),
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


def fetch_hero_data() -> Optional[dict]:
    try:
        conn = get_conn()
        cur = conn.cursor()

        # total workouts
        cur.execute("SELECT COUNT(*) AS cnt FROM hevy_workouts")
        total_workouts = cur.fetchone()["cnt"]

        # strength — max weight on leg press from last workout date
        cur.execute("""
            SELECT MAX(weight_kg) AS strength
            FROM hevy_sets
            WHERE workout_date = (SELECT MAX(workout_date) FROM hevy_sets)
              AND (
                LOWER(exercise_title) LIKE '%leg press%'
                OR LOWER(exercise_title) LIKE '%жим%ног%'
              )
        """)
        row = cur.fetchone()
        strength = row["strength"] if row and row["strength"] is not None else None

        if strength is None:
            cur.execute("""
                SELECT MAX(weight_kg) AS strength
                FROM hevy_sets
                WHERE workout_date = (SELECT MAX(workout_date) FROM hevy_sets)
            """)
            row = cur.fetchone()
            strength = float(row["strength"]) if row and row["strength"] is not None else 0.0
        else:
            strength = float(strength)

        # endurance — avg steps / 100 over last 7 days
        cur.execute("""
            SELECT COALESCE(AVG(steps), 0) AS avg_steps
            FROM health_daily_summary
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        row = cur.fetchone()
        endurance = float(row["avg_steps"]) / 100.0 if row else 0.0

        # recovery — avg total sleep (min) last 7 days (from Notion manual tracker)
        cur.execute("""
            SELECT COALESCE(AVG(sleep_duration_min), 0) AS avg_sleep
            FROM health_daily_summary
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        row = cur.fetchone()
        recovery = float(row["avg_sleep"]) if row else 0.0

        # volume — total volume last 30 days
        cur.execute("""
            SELECT COALESCE(SUM(total_volume_kg), 0) AS vol
            FROM hevy_workouts
            WHERE workout_date >= CURRENT_DATE - INTERVAL '30 days'
        """)
        row = cur.fetchone()
        volume = float(row["vol"]) if row else 0.0

        cur.close()
        conn.close()

        return {
            "total_workouts": int(total_workouts),
            "strength": strength,
            "endurance": endurance,
            "recovery": recovery,
            "volume": volume,
        }
    except Exception:
        traceback.print_exc()
        return None


def fetch_quest_data() -> Optional[dict]:
    try:
        conn = get_conn()
        cur = conn.cursor()

        # all workout dates last 60 days
        cur.execute("""
            SELECT workout_date
            FROM hevy_workouts
            WHERE workout_date >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY workout_date DESC
        """)
        rows = cur.fetchall()
        workout_dates = [r["workout_date"] for r in rows]

        # total workouts
        cur.execute("SELECT COUNT(*) AS cnt FROM hevy_workouts")
        total_workouts = int(cur.fetchone()["cnt"])

        # recent sleep — use sleep_duration_min (total sleep, from Notion manual tracker)
        cur.execute("""
            SELECT date, sleep_duration_min
            FROM health_daily_summary
            ORDER BY date DESC
            LIMIT 14
        """)
        recent_sleep = [(r["date"], r["sleep_duration_min"]) for r in cur.fetchall()]

        # current week volume
        cur.execute("""
            SELECT COALESCE(SUM(total_volume_kg), 0) AS vol
            FROM hevy_workouts
            WHERE workout_date >= date_trunc('week', CURRENT_DATE)
        """)
        current_week_volume = float(cur.fetchone()["vol"])

        # max weekly volume ever
        cur.execute("""
            SELECT COALESCE(MAX(weekly_vol), 0) AS max_vol
            FROM (
                SELECT date_trunc('week', workout_date) AS wk, SUM(total_volume_kg) AS weekly_vol
                FROM hevy_workouts
                GROUP BY wk
            ) sub
        """)
        max_weekly_volume = float(cur.fetchone()["max_vol"])

        # last workout date
        cur.execute("SELECT MAX(workout_date) AS last_dt FROM hevy_workouts")
        row = cur.fetchone()
        last_workout_date = row["last_dt"] if row else None

        # weight measurements count in last 7 days
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM body_measurements
            WHERE measured_at >= CURRENT_DATE - INTERVAL '7 days'
        """)
        weight_measurements_7d = int(cur.fetchone()["cnt"])

        # current month volume
        cur.execute("""
            SELECT COALESCE(SUM(total_volume_kg), 0) AS vol
            FROM hevy_workouts
            WHERE date_trunc('month', workout_date) = date_trunc('month', CURRENT_DATE)
        """)
        current_month_volume = float(cur.fetchone()["vol"])

        # avg volume of last 3 completed months
        cur.execute("""
            SELECT COALESCE(AVG(monthly_vol), 0) AS avg_vol
            FROM (
                SELECT SUM(total_volume_kg) AS monthly_vol
                FROM hevy_workouts
                WHERE workout_date >= CURRENT_DATE - INTERVAL '4 months'
                  AND date_trunc('month', workout_date) < date_trunc('month', CURRENT_DATE)
                GROUP BY date_trunc('month', workout_date)
                ORDER BY date_trunc('month', workout_date) DESC
                LIMIT 3
            ) sub
        """)
        avg_monthly_volume_3m = float(cur.fetchone()["avg_vol"])

        # leg press: last 2 session max weights
        cur.execute("""
            SELECT MAX(weight_kg) AS max_w
            FROM hevy_sets
            WHERE LOWER(exercise_title) LIKE '%жим%ног%'
               OR LOWER(exercise_title) LIKE '%leg press%'
            GROUP BY workout_date
            ORDER BY workout_date DESC
            LIMIT 2
        """)
        leg_press_rows = [float(r["max_w"]) for r in cur.fetchall() if r["max_w"] is not None]
        leg_press_current = leg_press_rows[0] if len(leg_press_rows) > 0 else 0.0
        leg_press_prev = leg_press_rows[1] if len(leg_press_rows) > 1 else 0.0

        cur.close()
        conn.close()

        return {
            "workout_dates": workout_dates,
            "total_workouts": total_workouts,
            "recent_sleep": recent_sleep,
            "current_week_volume": current_week_volume,
            "max_weekly_volume": max_weekly_volume,
            "last_workout_date": last_workout_date,
            "weight_measurements_7d": weight_measurements_7d,
            "current_month_volume": current_month_volume,
            "avg_monthly_volume_3m": avg_monthly_volume_3m,
            "leg_press_current": leg_press_current,
            "leg_press_prev": leg_press_prev,
        }
    except Exception:
        traceback.print_exc()
        return None


def fetch_boss_data() -> Optional[dict]:
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT weight
            FROM body_measurements
            ORDER BY measured_at DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        current_weight = float(row["weight"]) if row and row["weight"] is not None else None

        cur.close()
        conn.close()

        return {"current_weight": current_weight}
    except Exception:
        traceback.print_exc()
        return None


def fetch_stats_data() -> Optional[dict]:
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT weight, body_fat
            FROM body_measurements
            ORDER BY measured_at DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        current_weight = float(row["weight"]) if row and row["weight"] is not None else None
        current_body_fat = float(row["body_fat"]) if row and row.get("body_fat") is not None else None

        cur.execute("SELECT COUNT(*) AS cnt FROM hevy_workouts")
        total_workouts = int(cur.fetchone()["cnt"])

        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM hevy_workouts
            WHERE workout_date >= CURRENT_DATE - INTERVAL '30 days'
        """)
        workouts_30d = int(cur.fetchone()["cnt"])

        cur.execute("SELECT COALESCE(SUM(total_volume_kg), 0) AS vol FROM hevy_workouts")
        total_volume = float(cur.fetchone()["vol"])

        cur.execute("""
            SELECT workout_date, total_volume_kg
            FROM hevy_workouts
            ORDER BY total_volume_kg DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        best_workout = None
        if row:
            best_workout = {
                "workout_date": str(row["workout_date"]),
                "total_volume_kg": float(row["total_volume_kg"]),
            }

        cur.execute("""
            SELECT AVG(total_volume_kg) AS avg_vol
            FROM (
                SELECT total_volume_kg
                FROM hevy_workouts
                ORDER BY workout_date DESC
                LIMIT 5
            ) sub
        """)
        row = cur.fetchone()
        avg_volume_5 = float(row["avg_vol"]) if row and row["avg_vol"] is not None else None

        cur.execute("""
            SELECT workout_date
            FROM hevy_workouts
            ORDER BY workout_date DESC
        """)
        all_dates = [r["workout_date"] for r in cur.fetchall()]

        cur.close()
        conn.close()

        current_streak_weeks = _compute_streak_weeks(all_dates)

        return {
            "current_weight": current_weight,
            "current_body_fat": current_body_fat,
            "total_workouts": total_workouts,
            "workouts_30d": workouts_30d,
            "total_volume": total_volume,
            "best_workout": best_workout,
            "avg_volume_5": avg_volume_5,
            "current_streak_weeks": current_streak_weeks,
        }
    except Exception:
        traceback.print_exc()
        return None


def _compute_streak_weeks(workout_dates) -> int:
    if not workout_dates:
        return 0

    import datetime

    week_set = set()
    for d in workout_dates:
        if hasattr(d, "isocalendar"):
            iso = d.isocalendar()
        else:
            iso = datetime.date.fromisoformat(str(d)).isocalendar()
        week_set.add((iso[0], iso[1]))

    most_recent = workout_dates[0]
    if hasattr(most_recent, "isocalendar"):
        current = most_recent
    else:
        current = datetime.date.fromisoformat(str(most_recent))

    streak = 0
    check_date = current
    while True:
        iso = check_date.isocalendar()
        key = (iso[0], iso[1])
        if key in week_set:
            streak += 1
            days_since_monday = check_date.weekday()
            check_date = check_date - datetime.timedelta(days=days_since_monday + 7)
        else:
            break

    return streak


def fetch_events_data() -> Optional[list]:
    try:
        conn = get_conn()
        cur = conn.cursor()

        events = []

        cur.execute("""
            SELECT
                workout_date,
                workout_title,
                total_volume_kg,
                LAG(total_volume_kg) OVER (ORDER BY workout_date) AS prev_vol
            FROM hevy_workouts
            ORDER BY workout_date DESC
            LIMIT 10
        """)
        for row in cur.fetchall():
            events.append({
                "type": "workout",
                "date": row["workout_date"],
                "title": row["workout_title"],
                "volume": float(row["total_volume_kg"]) if row["total_volume_kg"] is not None else 0.0,
                "prev_vol": float(row["prev_vol"]) if row["prev_vol"] is not None else None,
            })

        cur.execute("""
            SELECT DATE(measured_at) AS date, weight
            FROM body_measurements
            ORDER BY measured_at DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            events.append({
                "type": "weight",
                "date": row["date"],
                "weight": float(row["weight"]) if row["weight"] is not None else 0.0,
            })

        # Sleep events — sleep_duration_min (total sleep from Notion manual tracker)
        cur.execute("""
            SELECT date, sleep_duration_min
            FROM health_daily_summary
            WHERE sleep_duration_min > 0
            ORDER BY date DESC
            LIMIT 10
        """)
        for row in cur.fetchall():
            events.append({
                "type": "sleep",
                "date": row["date"],
                "sleep_min": int(row["sleep_duration_min"]) if row["sleep_duration_min"] is not None else 0,
            })

        cur.execute("""
            WITH ranked AS (
                SELECT
                    exercise_title,
                    workout_date,
                    MAX(weight_kg) AS max_weight,
                    MAX(MAX(weight_kg)) OVER (
                        PARTITION BY exercise_title
                        ORDER BY workout_date
                        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                    ) AS prev_max
                FROM hevy_sets
                GROUP BY exercise_title, workout_date
            )
            SELECT exercise_title, workout_date, max_weight
            FROM ranked
            WHERE max_weight > COALESCE(prev_max, 0)
              AND workout_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY workout_date DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            events.append({
                "type": "record",
                "date": row["workout_date"],
                "exercise": row["exercise_title"],
                "weight": float(row["max_weight"]) if row["max_weight"] is not None else 0.0,
            })

        cur.close()
        conn.close()

        return events
    except Exception:
        traceback.print_exc()
        return None


def fetch_weight_chart_data() -> Optional[list]:
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT DATE(measured_at) AS date, AVG(weight)::float AS weight
            FROM body_measurements
            WHERE measured_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(measured_at)
            ORDER BY date
        """)
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return [{"date": str(r["date"]), "weight": float(r["weight"])} for r in rows]
    except Exception:
        traceback.print_exc()
        return None
