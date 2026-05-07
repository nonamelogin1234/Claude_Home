from __future__ import annotations

import logging
from datetime import date
from typing import Any

from config import BOSSES, Settings
from db import Database
from progress import (
    boss_progress,
    calculate_level,
    calculate_week_streak,
    current_max_gap_days,
    current_sleep_streak,
    maybe_float,
    resolve_active_boss,
)


logger = logging.getLogger(__name__)


class TrackerRepository:
    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def get_hero_payload(self) -> dict[str, Any]:
        summary = self.db.fetch_one(
            """
            WITH latest_workout AS (
                SELECT MAX(workout_date::date) AS workout_date
                FROM hevy_workouts
            ),
            latest_leg_press AS (
                SELECT MAX(weight_kg) AS max_leg_press
                FROM hevy_sets
                WHERE workout_date::date = (SELECT workout_date FROM latest_workout)
                  AND LOWER(exercise_title) LIKE '%%жим ног%%'
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
                COALESCE((SELECT total_volume_kg FROM monthly_volume), 0) AS volume_value
            """
        )
        if summary is None:
            logger.info("Hero summary query returned no rows; using zero fallback")
            summary = {
                "total_workouts": 0,
                "last_workout_date": None,
                "strength_value": 0,
                "endurance_value": 0,
                "recovery_value": 0,
                "volume_value": 0,
            }

        total_workouts = int(summary["total_workouts"] or 0)
        level, rank_title, next_rank_title, progress_percent, workouts_to_next = calculate_level(total_workouts)

        return {
            "name": self.settings.hero_name,
            "class": self.settings.hero_class,
            "level": level,
            "rank_title": rank_title,
            "total_workouts": total_workouts,
            "progress_percent": progress_percent,
            "workouts_to_next_level": workouts_to_next,
            "next_rank_title": next_rank_title,
            "last_workout_date": summary["last_workout_date"],
            "stats": [
                {
                    "name": "Сила",
                    "value": float(summary["strength_value"] or 0),
                    "display_value": f"{float(summary['strength_value'] or 0):.1f} кг",
                    "unit": "kg",
                },
                {
                    "name": "Выносливость",
                    "value": round(float(summary["endurance_value"] or 0), 1),
                    "display_value": f"{round(float(summary['endurance_value'] or 0), 1):.1f}",
                    "unit": "pts",
                },
                {
                    "name": "Восстановление",
                    "value": round(float(summary["recovery_value"] or 0), 1),
                    "display_value": f"{round(float(summary['recovery_value'] or 0), 1):.0f} мин",
                    "unit": "min",
                },
                {
                    "name": "Объём",
                    "value": float(summary["volume_value"] or 0),
                    "display_value": f"{float(summary['volume_value'] or 0):.0f} кг",
                    "unit": "kg",
                },
            ],
        }

    def get_stats_payload(self) -> dict[str, Any]:
        stats = self.db.fetch_one(
            """
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
                COALESCE((SELECT avg_volume FROM recent_five), 0) AS average_last_5_workouts_kg
            """
        ) or {}

        return {
            "current_weight": maybe_float(stats.get("current_weight")),
            "current_weight_date": stats.get("current_weight_date"),
            "total_workouts": int(stats.get("total_workouts") or 0),
            "workouts_last_30_days": int(stats.get("workouts_last_30_days") or 0),
            "current_week_streak": self._calculate_week_streak(),
            "total_volume_kg": float(stats.get("total_volume_kg") or 0),
            "record_workout_date": stats.get("record_workout_date"),
            "record_workout_volume_kg": maybe_float(stats.get("record_workout_volume_kg")),
            "average_last_5_workouts_kg": float(stats.get("average_last_5_workouts_kg") or 0),
        }

    def get_weight_chart_payload(self) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT measured_at::date AS date, weight
            FROM body_measurements
            WHERE measured_at::date >= CURRENT_DATE - INTERVAL '29 days'
            ORDER BY measured_at::date ASC
            """
        )

    def get_bosses_payload(self) -> list[dict[str, Any]]:
        weight_row = self.db.fetch_one(
            """
            SELECT
                (
                    SELECT weight
                    FROM body_measurements
                    ORDER BY measured_at DESC
                    LIMIT 1
                ) AS current_weight,
                (
                    SELECT MAX(weight)
                    FROM body_measurements
                ) AS start_weight
            """
        ) or {"current_weight": None, "start_weight": None}

        current_weight = maybe_float(weight_row.get("current_weight"))
        start_weight = maybe_float(weight_row.get("start_weight")) or current_weight or 117.0
        active_slug = resolve_active_boss(current_weight)

        bosses: list[dict[str, Any]] = []
        for slug, icon, title, target in BOSSES:
            if current_weight is not None and current_weight <= target:
                status = "completed"
                subtitle = "Порог уже пройден"
            elif slug == active_slug:
                status = "active"
                delta = (current_weight - target) if current_weight is not None else None
                subtitle = f"Осталось {delta:.1f} кг до победы" if delta is not None else "Ждём актуальный вес"
            else:
                status = "locked"
                subtitle = "Сначала победите предыдущего босса"

            bosses.append(
                {
                    "slug": slug,
                    "icon": icon,
                    "title": title,
                    "target_weight": target,
                    "current_weight": current_weight,
                    "status": status,
                    "progress_percent": boss_progress(start_weight, current_weight, target),
                    "subtitle": subtitle,
                }
            )

        return bosses

    def get_quests_payload(self) -> list[dict[str, Any]]:
        total_workouts_row = self.db.fetch_one("SELECT COUNT(*) AS total_workouts FROM hevy_workouts") or {"total_workouts": 0}
        total_workouts = int(total_workouts_row["total_workouts"] or 0)
        week_streak = self._calculate_week_streak()
        workout_gap_days = self._current_max_gap_days()
        sleep_streak = self._current_sleep_streak()
        volume_progress = self._weekly_volume_progress()

        return [
            {
                "slug": "warrior_no_gaps",
                "icon": "⚔️",
                "title": "Воин без пропусков",
                "description": "Поддерживать серию недель с тренировками без провалов длиннее 4 дней.",
                "status": "active" if week_streak > 0 and workout_gap_days <= 4 else "locked",
                "progress_percent": min((week_streak / 4) * 100, 100),
                "progress_label": f"{week_streak} нед. подряд, макс. пауза {workout_gap_days} дн.",
                "category": "active",
            },
            {
                "slug": "sleep_guardian",
                "icon": "🌙",
                "title": "Страж сна",
                "description": "Собрать 5 ночей подряд с глубоким сном более 120 минут.",
                "status": "completed" if sleep_streak >= 5 else ("active" if sleep_streak > 0 else "locked"),
                "progress_percent": min((sleep_streak / 5) * 100, 100),
                "progress_label": f"{sleep_streak}/5 ночей",
                "category": "active",
            },
            {
                "slug": "volume_conqueror",
                "icon": "🏆",
                "title": "Покоритель объёма",
                "description": "Побить лучший недельный объём тренировок.",
                "status": volume_progress["status"],
                "progress_percent": volume_progress["progress_percent"],
                "progress_label": volume_progress["label"],
                "category": "active",
            },
            {
                "slug": "faithful_path",
                "icon": "🧭",
                "title": "Верный путь",
                "description": "Дойти до 10 недель подряд, не пропуская целую неделю.",
                "status": "completed" if week_streak >= 10 else ("active" if week_streak > 0 else "locked"),
                "progress_percent": min((week_streak / 10) * 100, 100),
                "progress_label": f"{week_streak}/10 недель",
                "category": "active",
            },
            {
                "slug": "first_step",
                "icon": "🥾",
                "title": "Первый шаг",
                "description": "Провести хотя бы одну тренировку.",
                "status": "completed" if total_workouts >= 1 else "locked",
                "progress_percent": 100 if total_workouts >= 1 else 0,
                "progress_label": f"{min(total_workouts, 1)}/1",
                "category": "archive",
            },
            {
                "slug": "gym_veteran",
                "icon": "🛡️",
                "title": "Ветеран зала",
                "description": "Набрать 10 тренировок в журнале.",
                "status": "completed" if total_workouts >= 10 else "locked",
                "progress_percent": min((total_workouts / 10) * 100, 100),
                "progress_label": f"{total_workouts}/10 тренировок",
                "category": "archive",
            },
            {
                "slug": "iron_man",
                "icon": "⛓️",
                "title": "Железный человек",
                "description": "Набрать 25 тренировок в журнале.",
                "status": "completed" if total_workouts >= 25 else "locked",
                "progress_percent": min((total_workouts / 25) * 100, 100),
                "progress_label": f"{total_workouts}/25 тренировок",
                "category": "archive",
            },
        ]

    def get_events_payload(self, limit: int = 15) -> list[dict[str, Any]]:
        workouts = self.db.fetch_all(
            """
            WITH ranked AS (
                SELECT
                    workout_date::date AS event_date,
                    total_volume_kg,
                    LAG(total_volume_kg) OVER (ORDER BY workout_date::date) AS prev_volume
                FROM hevy_workouts
            )
            SELECT event_date, total_volume_kg, prev_volume
            FROM ranked
            ORDER BY event_date DESC
            LIMIT 15
            """
        )
        weights = self.db.fetch_all(
            """
            SELECT measured_at::date AS event_date, weight
            FROM body_measurements
            ORDER BY measured_at DESC
            LIMIT 15
            """
        )
        sleeps = self.db.fetch_all(
            """
            SELECT date AS event_date, deep_sleep_min
            FROM health_daily_summary
            WHERE COALESCE(deep_sleep_min, 0) > 120
            ORDER BY date DESC
            LIMIT 15
            """
        )
        records = self.db.fetch_all(
            """
            WITH ordered_sets AS (
                SELECT
                    workout_date::date AS event_date,
                    exercise_title,
                    weight_kg,
                    reps,
                    set_index,
                    MAX(weight_kg) OVER (
                        PARTITION BY exercise_title
                        ORDER BY workout_date::date, set_index
                        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                    ) AS previous_best
                FROM hevy_sets
            )
            SELECT event_date, exercise_title, weight_kg, reps
            FROM ordered_sets
            WHERE weight_kg > COALESCE(previous_best, -1)
            ORDER BY event_date DESC, weight_kg DESC
            LIMIT 15
            """
        )

        events: list[dict[str, Any]] = []
        for row in workouts:
            total_volume = float(row["total_volume_kg"] or 0)
            prev_volume = row.get("prev_volume")
            delta_text = ""
            if prev_volume not in (None, 0):
                delta = ((total_volume - float(prev_volume)) / float(prev_volume)) * 100
                sign = "+" if delta >= 0 else ""
                delta_text = f" ({sign}{delta:.1f}% к прошлой)"
            events.append(
                {
                    "date": row["event_date"],
                    "icon": "⚔️",
                    "title": "Тренировка завершена",
                    "description": f"Воин завершил тренировку. Объём: {total_volume:.0f} кг{delta_text}",
                    "category": "workout",
                }
            )

        for row in weights:
            weight = float(row["weight"] or 0)
            events.append(
                {
                    "date": row["event_date"],
                    "icon": "⚖️",
                    "title": "Вес обновлён",
                    "description": f"Вес зафиксирован: {weight:.1f} кг",
                    "category": "weight",
                }
            )

        for row in sleeps:
            deep_sleep = int(row["deep_sleep_min"] or 0)
            events.append(
                {
                    "date": row["event_date"],
                    "icon": "🌙",
                    "title": "Ночь отдыха",
                    "description": f"Ночь отдыха. Глубокий сон: {deep_sleep} мин",
                    "category": "sleep",
                }
            )

        seen_records: set[tuple[date, str]] = set()
        for row in records:
            key = (row["event_date"], row["exercise_title"])
            if key in seen_records:
                continue
            seen_records.add(key)
            events.append(
                {
                    "date": row["event_date"],
                    "icon": "🏆",
                    "title": "Новый рекорд",
                    "description": f"Новый рекорд: {row['exercise_title']} — {float(row['weight_kg'] or 0):.1f} кг × {int(row['reps'] or 0)}",
                    "category": "record",
                }
            )

        events.sort(key=lambda item: item["date"], reverse=True)
        return events[:limit]

    def health_status(self) -> dict[str, Any]:
        return {
            "db": "ok" if self.db.ping() else "error",
        }

    def _calculate_week_streak(self) -> int:
        rows = self.db.fetch_all(
            """
            SELECT DISTINCT DATE_TRUNC('week', workout_date::date)::date AS week_start
            FROM hevy_workouts
            ORDER BY week_start DESC
            """
        )
        return calculate_week_streak([row["week_start"] for row in rows])

    def _current_max_gap_days(self) -> int:
        rows = self.db.fetch_all(
            """
            SELECT workout_date::date AS workout_date
            FROM hevy_workouts
            ORDER BY workout_date DESC
            LIMIT 12
            """
        )
        return current_max_gap_days([row["workout_date"] for row in rows])

    def _current_sleep_streak(self) -> int:
        rows = self.db.fetch_all(
            """
            SELECT date, deep_sleep_min
            FROM health_daily_summary
            ORDER BY date DESC
            LIMIT 14
            """
        )
        return current_sleep_streak(rows)

    def _weekly_volume_progress(self) -> dict[str, Any]:
        row = self.db.fetch_one(
            """
            WITH weekly AS (
                SELECT
                    DATE_TRUNC('week', workout_date::date)::date AS week_start,
                    SUM(COALESCE(total_volume_kg, 0)) AS week_volume
                FROM hevy_workouts
                GROUP BY 1
            ),
            ranked AS (
                SELECT
                    week_start,
                    week_volume,
                    MAX(week_volume) OVER () AS best_volume,
                    MAX(week_volume) FILTER (
                        WHERE week_start < DATE_TRUNC('week', CURRENT_DATE)::date
                    ) OVER () AS previous_best
                FROM weekly
            )
            SELECT
                COALESCE(MAX(week_volume) FILTER (
                    WHERE week_start = DATE_TRUNC('week', CURRENT_DATE)::date
                ), 0) AS current_week_volume,
                COALESCE(MAX(previous_best), 0) AS previous_best
            FROM ranked
            """
        )
        if row is None:
            logger.info("Weekly volume query returned no rows; using zero fallback")
            row = {"current_week_volume": 0, "previous_best": 0}

        current_volume = float(row["current_week_volume"] or 0)
        previous_best = float(row["previous_best"] or 0)

        if current_volume <= 0 and previous_best <= 0:
            return {"status": "locked", "progress_percent": 0.0, "label": "Недостаточно данных"}
        if previous_best <= 0:
            return {"status": "active", "progress_percent": 100.0, "label": f"Первая полная неделя: {current_volume:.0f} кг"}
        if current_volume > previous_best:
            return {"status": "completed", "progress_percent": 100.0, "label": f"Новый рекорд недели: {current_volume:.0f} кг"}

        progress = min((current_volume / previous_best) * 100, 100)
        return {
            "status": "active" if current_volume > 0 else "locked",
            "progress_percent": progress,
            "label": f"{current_volume:.0f} / {previous_best:.0f} кг",
        }
