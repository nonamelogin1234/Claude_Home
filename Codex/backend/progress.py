from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from config import BOSSES, LEVELS


def calculate_level(total_workouts: int) -> tuple[int, str, str | None, float, int]:
    if total_workouts <= 0:
        return 0, "Пробуждение", "Новобранец", 0.0, 1

    for level, low, high, title, next_title in LEVELS:
        if high is None and total_workouts >= low:
            return level, title, next_title, 100.0, 0
        if high is not None and low <= total_workouts <= high:
            span = max(high - low + 1, 1)
            progress = ((total_workouts - low + 1) / span) * 100
            workouts_to_next = max(high - total_workouts, 0)
            return level, title, next_title, round(progress, 1), workouts_to_next

    return 0, "Пробуждение", "Новобранец", 0.0, 1


def calculate_week_streak(weeks: list[date]) -> int:
    if not weeks:
        return 0

    streak = 0
    previous_week: date | None = None
    for week_start in weeks:
        if previous_week is None:
            streak = 1
            previous_week = week_start
            continue

        if previous_week - week_start == timedelta(days=7):
            streak += 1
            previous_week = week_start
        else:
            break

    return streak


def current_max_gap_days(workout_dates: list[date]) -> int:
    if len(workout_dates) < 2:
        return 0

    gaps = []
    for current, previous in zip(workout_dates, workout_dates[1:]):
        gaps.append(abs((current - previous).days))
    return max(gaps, default=0)


def current_sleep_streak(sleep_rows: list[dict[str, Any]]) -> int:
    streak = 0
    prev_date: date | None = None
    for row in sleep_rows:
        current_date = row["date"]
        deep_sleep = int(row["deep_sleep_min"] or 0)
        if deep_sleep <= 120:
            break
        if prev_date is not None and (prev_date - current_date).days != 1:
            break
        streak += 1
        prev_date = current_date
    return streak


def boss_progress(start_weight: float | None, current_weight: float | None, target_weight: float) -> float:
    if current_weight is None or start_weight is None:
        return 0.0

    denominator = start_weight - target_weight
    if denominator < 0:
        return 100.0 if current_weight <= target_weight else 0.0
    if denominator == 0:
        return 100.0 if current_weight < target_weight else 0.0

    progress = ((start_weight - current_weight) / denominator) * 100
    return max(0.0, min(progress, 100.0))


def maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def resolve_active_boss(current_weight: float | None) -> str | None:
    for slug, _, _, target in BOSSES:
        if current_weight is None or current_weight > target:
            return slug
    return None
