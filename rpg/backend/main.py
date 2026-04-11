import datetime
import os
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import cache
import db
from models import Boss, Event, HeroStats, Quest, WeightPoint

app = FastAPI(title="RPG Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = "/app/frontend"

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ─── Level thresholds ────────────────────────────────────────────────────────
LEVELS = [
    (1, 0, 10, "Начало"),
    (2, 10, 25, "На ходу"),
    (3, 25, 50, "В ритме"),
    (4, 50, 100, "Форма"),
    (5, 100, 999999, "Образ жизни"),
]


def compute_level(workouts: int):
    for lvl, prev_thr, next_thr, name in LEVELS:
        if workouts < next_thr or lvl == 5:
            return lvl, name, prev_thr, next_thr
    return 5, "Образ жизни", 100, 999999


# ─── /api/hero ───────────────────────────────────────────────────────────────
@app.get("/api/hero", response_model=HeroStats)
def get_hero():
    cached = cache.get("hero")
    if cached:
        return cached

    data = db.fetch_hero_data()
    if not data:
        data = {
            "total_workouts": 0,
            "strength": 0.0,
            "endurance": 0.0,
            "recovery": 0.0,
            "volume": 0.0,
        }

    workouts_count = data["total_workouts"]
    level, level_name, prev_thr, next_thr = compute_level(workouts_count)

    hero = HeroStats(
        name="СЕРГЕЙ",
        class_name="Путь трансформации",
        level=level,
        level_name=level_name,
        workouts_count=workouts_count,
        next_level_threshold=next_thr,
        prev_level_threshold=prev_thr,
        strength=data["strength"],
        endurance=data["endurance"],
        recovery=data["recovery"],
        volume=data["volume"],
    )

    cache.set("hero", hero.dict())
    return hero


# ─── /api/quests ─────────────────────────────────────────────────────────────
@app.get("/api/quests", response_model=List[Quest])
def get_quests():
    cached = cache.get("quests")
    if cached:
        return cached

    data = db.fetch_quest_data()
    if not data:
        data = {
            "workout_dates": [],
            "total_workouts": 0,
            "recent_sleep": [],
            "current_week_volume": 0.0,
            "max_weekly_volume": 0.0,
            "last_workout_date": None,
            "weight_measurements_7d": 0,
            "current_month_volume": 0.0,
            "avg_monthly_volume_3m": 0.0,
            "leg_press_current": 0.0,
            "leg_press_prev": 0.0,
        }

    today = datetime.date.today()
    workout_dates = data["workout_dates"]
    total_workouts = data["total_workouts"]
    recent_sleep = data["recent_sleep"]
    current_week_volume = data["current_week_volume"]
    max_weekly_volume = data["max_weekly_volume"]
    last_workout_date = data["last_workout_date"]
    weight_measurements_7d = data.get("weight_measurements_7d", 0)
    current_month_volume = data.get("current_month_volume", 0.0)
    avg_monthly_volume_3m = data.get("avg_monthly_volume_3m", 0.0)
    leg_press_current = data.get("leg_press_current", 0.0)
    leg_press_prev = data.get("leg_press_prev", 0.0)

    quests = []

    # ── Quest 1: Постоянство ─────────────────────────────────────────────────
    days_since_last = None
    if last_workout_date:
        if hasattr(last_workout_date, "toordinal"):
            ld = last_workout_date
        else:
            ld = datetime.date.fromisoformat(str(last_workout_date))
        days_since_last = (today - ld).days

    dates_30d = sorted(
        [d for d in workout_dates if (today - (d if hasattr(d, "toordinal") else datetime.date.fromisoformat(str(d)))).days <= 30],
        reverse=True,
    )

    no_big_gap = True
    if len(dates_30d) >= 2:
        for i in range(len(dates_30d) - 1):
            d1 = dates_30d[i] if hasattr(dates_30d[i], "toordinal") else datetime.date.fromisoformat(str(dates_30d[i]))
            d2 = dates_30d[i + 1] if hasattr(dates_30d[i + 1], "toordinal") else datetime.date.fromisoformat(str(dates_30d[i + 1]))
            if (d1 - d2).days > 4:
                no_big_gap = False
                break
    elif len(dates_30d) == 0:
        no_big_gap = False

    last_ok = days_since_last is not None and days_since_last <= 4
    if days_since_last is not None and days_since_last <= 4:
        q1_progress = max(0.0, (4 - days_since_last) / 4)
    else:
        q1_progress = 0.0

    quests.append(Quest(
        id="no_skip",
        icon="🔁",
        name="Постоянство",
        description="Нет пропусков больше 4 дней за 30 дней",
        status="active" if not (no_big_gap and last_ok) else "active",
        progress=round(q1_progress, 3),
        progress_text=f"{days_since_last if days_since_last is not None else '?'} дн. с последней тренировки",
    ))

    # ── Quest 2: Страж сна ───────────────────────────────────────────────────
    sleep_streak = 0
    for _, deep_sleep in recent_sleep:
        if deep_sleep is not None and int(deep_sleep) > 120:
            sleep_streak += 1
        else:
            break

    q2_progress = min(sleep_streak, 5) / 5.0
    q2_status = "completed" if sleep_streak >= 5 else "active"
    quests.append(Quest(
        id="sleep_guard",
        icon="🌙",
        name="Страж сна",
        description="5 ночей подряд глубокого сна более 120 мин",
        status=q2_status,
        progress=round(q2_progress, 3),
        progress_text=f"{sleep_streak}/5 ночей подряд",
    ))

    # ── Quest 3: Рекорд недели ───────────────────────────────────────────────
    if max_weekly_volume > 0:
        q3_progress = min(1.0, current_week_volume / max_weekly_volume)
        q3_status = "completed" if current_week_volume >= max_weekly_volume else "active"
    else:
        q3_progress = 0.0
        q3_status = "active"

    quests.append(Quest(
        id="volume_conqueror",
        icon="📦",
        name="Рекорд недели",
        description="Превзойти рекордную неделю по объёму",
        status=q3_status,
        progress=round(q3_progress, 3),
        progress_text=f"{current_week_volume:.0f} / {max_weekly_volume:.0f} кг",
    ))

    # ── Quest 4: Верный путь ─────────────────────────────────────────────────
    last_10 = workout_dates[:10]

    def get_week_start(d):
        dd = d if hasattr(d, "toordinal") else datetime.date.fromisoformat(str(d))
        return dd - datetime.timedelta(days=dd.weekday())

    if last_10:
        weeks_in_span = set(get_week_start(d) for d in last_10)
        if len(last_10) >= 2:
            first_d = last_10[-1] if hasattr(last_10[-1], "toordinal") else datetime.date.fromisoformat(str(last_10[-1]))
            last_d = last_10[0] if hasattr(last_10[0], "toordinal") else datetime.date.fromisoformat(str(last_10[0]))
            current_w = get_week_start(first_d)
            all_weeks_ok = True
            while current_w <= get_week_start(last_d):
                if current_w not in weeks_in_span:
                    all_weeks_ok = False
                    break
                current_w += datetime.timedelta(weeks=1)
        else:
            all_weeks_ok = True
    else:
        all_weeks_ok = False

    q4_progress = min(len(last_10), 10) / 10.0
    q4_status = "active" if not (all_weeks_ok and len(last_10) >= 10) else "completed"
    quests.append(Quest(
        id="steady_path",
        icon="🎯",
        name="Верный путь",
        description="10 тренировок без пропущенных недель",
        status=q4_status,
        progress=round(q4_progress, 3),
        progress_text=f"{min(len(last_10), 10)}/10 тренировок",
    ))

    # ── Quest 5: Первый шаг ──────────────────────────────────────────────────
    quests.append(Quest(
        id="first_step",
        icon="🌟",
        name="Первый шаг",
        description="Первая тренировка завершена",
        status="completed" if total_workouts >= 1 else "locked",
        progress=1.0 if total_workouts >= 1 else 0.0,
        progress_text="достигнуто" if total_workouts >= 1 else "0/1",
    ))

    # ── Quest 6: В ритме ─────────────────────────────────────────────────────
    quests.append(Quest(
        id="veteran",
        icon="🏅",
        name="В ритме",
        description="10 тренировок выполнено",
        status="completed" if total_workouts >= 10 else "active",
        progress=min(1.0, total_workouts / 10.0),
        progress_text=f"{total_workouts}/10 тренировок",
    ))

    # ── Quest 7: Марафон зала ────────────────────────────────────────────────
    quests.append(Quest(
        id="iron_man",
        icon="💪",
        name="Марафон зала",
        description="25 тренировок выполнено",
        status="completed" if total_workouts >= 25 else "active",
        progress=min(1.0, total_workouts / 25.0),
        progress_text=f"{total_workouts}/25 тренировок",
    ))

    # ── Quest 8: Пятничный ритуал ────────────────────────────────────────────
    workout_dates_set = set()
    for d in workout_dates:
        dd = d if hasattr(d, "toordinal") else datetime.date.fromisoformat(str(d))
        workout_dates_set.add(dd)

    last_4_fridays = []
    d = today
    while len(last_4_fridays) < 4:
        if d.weekday() == 4:  # Friday
            last_4_fridays.append(d)
        d -= datetime.timedelta(days=1)

    friday_count = sum(1 for fd in last_4_fridays if fd in workout_dates_set)
    quests.append(Quest(
        id="friday_ritual",
        icon="🌆",
        name="Пятничный ритуал",
        description="Посетить зал в пятницу 4 недели подряд",
        status="completed" if friday_count >= 4 else "active",
        progress=round(friday_count / 4.0, 3),
        progress_text=f"{friday_count}/4 пятниц",
    ))

    # ── Quest 9: Без никотина ─────────────────────────────────────────────────
    quit_date = datetime.date(2025, 2, 13)
    nicotine_days = (today - quit_date).days
    quests.append(Quest(
        id="no_nicotine",
        icon="🚭",
        name="Без никотина",
        description="Дней без сигарет с 13 февраля 2025",
        status="active",
        progress=1.0,
        progress_text=f"{nicotine_days} дней",
    ))

    # ── Quest 10: Постоянство веса ───────────────────────────────────────────
    quests.append(Quest(
        id="weight_consistency",
        icon="⚖️",
        name="Постоянство веса",
        description="Взвешиваться минимум 5 раз за последние 7 дней",
        status="completed" if weight_measurements_7d >= 5 else "active",
        progress=round(min(weight_measurements_7d, 5) / 5.0, 3),
        progress_text=f"{weight_measurements_7d}/5 взвешиваний",
    ))

    # ── Quest 11: Объём месяца ────────────────────────────────────────────────
    if avg_monthly_volume_3m > 0:
        q11_progress = min(1.0, current_month_volume / avg_monthly_volume_3m)
        q11_status = "completed" if current_month_volume >= avg_monthly_volume_3m else "active"
    else:
        q11_progress = 0.0
        q11_status = "active"

    quests.append(Quest(
        id="monthly_volume_goal",
        icon="📈",
        name="Объём месяца",
        description="Набрать объём тренировок выше среднего за 3 месяца",
        status=q11_status,
        progress=round(q11_progress, 3),
        progress_text=f"{current_month_volume:.0f} / {avg_monthly_volume_3m:.0f} кг",
    ))

    # ── Quest 12: Серия сна ────────────────────────────────────────────────────
    sleep_streak_90 = 0
    for _, deep_sleep in recent_sleep:
        if deep_sleep is not None and int(deep_sleep) > 90:
            sleep_streak_90 += 1
        else:
            break

    q12_progress = min(sleep_streak_90, 7) / 7.0
    q12_status = "completed" if sleep_streak_90 >= 7 else "active"
    quests.append(Quest(
        id="sleep_quality_streak",
        icon="✨",
        name="Серия сна",
        description="7 ночей подряд с глубоким сном более 90 мин",
        status=q12_status,
        progress=round(q12_progress, 3),
        progress_text=f"{sleep_streak_90}/7 ночей подряд",
    ))

    # ── Quest 13: Первая сотня ───────────────────────────────────────────────
    quests.append(Quest(
        id="hundred_sessions",
        icon="💯",
        name="Первая сотня",
        description="Завершить 100 тренировок",
        status="completed" if total_workouts >= 100 else "active",
        progress=min(1.0, total_workouts / 100.0),
        progress_text=f"{total_workouts}/100 тренировок",
    ))

    # ── Quest 14: Рекорд жима ─────────────────────────────────────────────────
    if leg_press_current > 0 and leg_press_prev > 0:
        if leg_press_current > leg_press_prev:
            lp_status = "completed"
            lp_progress = 1.0
            lp_text = f"{leg_press_current:.0f} кг — новый рекорд"
        else:
            lp_status = "active"
            lp_progress = round(leg_press_current / leg_press_prev, 3)
            lp_text = f"{leg_press_current:.0f} / {leg_press_prev:.0f} кг"
    elif leg_press_current > 0:
        lp_status = "active"
        lp_progress = 0.5
        lp_text = f"текущий: {leg_press_current:.0f} кг"
    else:
        lp_status = "locked"
        lp_progress = 0.0
        lp_text = "нет данных"

    quests.append(Quest(
        id="leg_press_record",
        icon="🦵",
        name="Рекорд жима",
        description="Превысить личный рекорд в жиме ног",
        status=lp_status,
        progress=lp_progress,
        progress_text=lp_text,
    ))

    result = [q.dict() for q in quests]
    cache.set("quests", result)
    return result


# ─── /api/bosses ─────────────────────────────────────────────────────────────
BOSSES_DEF = [
    ("Первый порог — 110 кг", "⚖️", 110.0),
    ("Хранитель плато — 105 кг", "⚗️", 105.0),
    ("Ниже ста — 99 кг", "🎯", 99.0),
    ("Комфортный вес — 90 кг", "🌿", 90.0),
    ("Целевой вес — 85 кг", "✦", 85.0),
]

START_WEIGHT = 120.0


@app.get("/api/bosses", response_model=List[Boss])
def get_bosses():
    cached = cache.get("bosses")
    if cached:
        return cached

    data = db.fetch_boss_data()
    current_weight = data["current_weight"] if data and data["current_weight"] is not None else 120.0

    bosses = []
    active_set = False

    for name, icon, target in BOSSES_DEF:
        defeated = current_weight <= target

        if defeated:
            status = "defeated"
        elif not active_set:
            status = "active"
            active_set = True
        else:
            status = "locked"

        if START_WEIGHT == target:
            progress = 1.0 if defeated else 0.0
        else:
            progress = max(0.0, min(1.0, (START_WEIGHT - current_weight) / (START_WEIGHT - target)))

        bosses.append(Boss(
            name=name,
            icon=icon,
            target_weight=target,
            status=status,
            current_weight=current_weight,
            progress=round(progress, 3),
        ))

    result = [b.dict() for b in bosses]
    cache.set("bosses", result)
    return result


# ─── /api/stats ──────────────────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    cached = cache.get("stats")
    if cached:
        return cached

    data = db.fetch_stats_data()
    if not data:
        data = {
            "current_weight": None,
            "current_body_fat": None,
            "total_workouts": 0,
            "workouts_30d": 0,
            "total_volume": 0.0,
            "best_workout": None,
            "avg_volume_5": None,
            "current_streak_weeks": 0,
        }

    cache.set("stats", data)
    return data


# ─── /api/events ─────────────────────────────────────────────────────────────
@app.get("/api/events", response_model=List[Event])
def get_events():
    cached = cache.get("events")
    if cached:
        return cached

    raw = db.fetch_events_data()
    if not raw:
        raw = []

    def get_date(e):
        d = e.get("date")
        if d is None:
            return datetime.date.min
        if hasattr(d, "toordinal"):
            return d
        try:
            return datetime.date.fromisoformat(str(d))
        except Exception:
            return datetime.date.min

    raw_sorted = sorted(raw, key=get_date, reverse=True)[:15]

    events = []
    for e in raw_sorted:
        d = get_date(e)
        date_str = d.strftime("%d.%m") if d != datetime.date.min else "??"

        etype = e.get("type")
        if etype == "workout":
            vol = e.get("volume", 0.0)
            prev_vol = e.get("prev_vol")
            vol_str = f"{vol:.0f} кг"
            if prev_vol is not None and prev_vol > 0:
                pct = (vol - prev_vol) / prev_vol * 100
                sign = "+" if pct >= 0 else ""
                vol_str += f" ({sign}{pct:.1f}%)"
            events.append(Event(
                date_str=date_str,
                icon="🏋️",
                text=f"Тренировка завершена · {vol_str}",
            ))
        elif etype == "weight":
            weight = e.get("weight", 0.0)
            events.append(Event(
                date_str=date_str,
                icon="⚖️",
                text=f"Вес зафиксирован: {weight:.1f} кг",
            ))
        elif etype == "sleep":
            ds = e.get("deep_sleep", 0)
            if ds > 90:
                events.append(Event(
                    date_str=date_str,
                    icon="🌙",
                    text=f"Глубокий сон: {ds} мин",
                ))
            elif ds > 0:
                events.append(Event(
                    date_str=date_str,
                    icon="😴",
                    text=f"Сон: {ds} мин",
                ))
        elif etype == "record":
            exercise = e.get("exercise", "")
            weight = e.get("weight", 0.0)
            events.append(Event(
                date_str=date_str,
                icon="🏆",
                text=f"Рекорд: {exercise} — {weight:.1f} кг",
            ))

    result = [ev.dict() for ev in events]
    cache.set("events", result)
    return result


# ─── /api/weight-chart ───────────────────────────────────────────────────────
@app.get("/api/weight-chart", response_model=List[WeightPoint])
def get_weight_chart():
    cached = cache.get("weight_chart")
    if cached:
        return cached

    data = db.fetch_weight_chart_data()
    if not data:
        data = []

    result = [WeightPoint(date=d["date"], weight=d["weight"]).dict() for d in data]
    cache.set("weight_chart", result)
    return result
