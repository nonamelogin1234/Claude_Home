from __future__ import annotations

import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from cache import SimpleTTLCache
from config import Settings
from db import Database
from models import BossesResponse, EventsResponse, HeroResponse, QuestsResponse, StatsResponse, WeightChartResponse
from repository import TrackerRepository
from security import verify_api_key


UTC = timezone.utc
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="RPG Progress Tracker", version="1.0.0")
settings = Settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)

cache = SimpleTTLCache(ttl_seconds=settings.cache_ttl_seconds)
db = Database(settings)
repository = TrackerRepository(db=db, settings=settings)
api = APIRouter(prefix="/api", dependencies=[Depends(verify_api_key)])


def now_utc() -> datetime:
    return datetime.now(UTC)


def cached_response(key: str, loader: Callable[[], dict[str, Any]], fallback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    cached = cache.get(key)
    if cached is not None:
        return deepcopy(cached)

    try:
        payload = loader()
        cache.set(key, payload)
        return payload
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to load %s payload", key)
        stale = cache.get(key, allow_stale=True)
        if stale is not None:
            stale_payload = deepcopy(stale)
            stale_payload["meta"] = {
                **stale_payload["meta"],
                "source": "stale_cache",
                "stale": True,
                "message": "База данных временно недоступна, показаны последние сохранённые данные",
            }
            return stale_payload

        payload = fallback()
        payload["meta"]["message"] = "База данных временно недоступна"
        return payload


@api.get("/hero", response_model=HeroResponse)
def get_hero() -> dict[str, Any]:
    return cached_response(
        "hero",
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "live", "stale": False, "message": None},
            "hero": repository.get_hero_payload(),
        },
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "fallback", "stale": True, "message": None},
            "hero": {
                "name": settings.hero_name,
                "class": settings.hero_class,
                "level": 0,
                "rank_title": "Пробуждение",
                "total_workouts": 0,
                "progress_percent": 0.0,
                "workouts_to_next_level": 1,
                "next_rank_title": "Новобранец",
                "last_workout_date": None,
                "stats": [
                    {"name": "Сила", "value": 0, "display_value": "0.0 кг", "unit": "kg"},
                    {"name": "Выносливость", "value": 0, "display_value": "0.0", "unit": "pts"},
                    {"name": "Восстановление", "value": 0, "display_value": "0 мин", "unit": "min"},
                    {"name": "Объём", "value": 0, "display_value": "0 кг", "unit": "kg"},
                ],
            },
        },
    )


@api.get("/quests", response_model=QuestsResponse)
def get_quests() -> dict[str, Any]:
    return cached_response(
        "quests",
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "live", "stale": False, "message": None},
            "quests": repository.get_quests_payload(),
        },
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "fallback", "stale": True, "message": None},
            "quests": [],
        },
    )


@api.get("/bosses", response_model=BossesResponse)
def get_bosses() -> dict[str, Any]:
    return cached_response(
        "bosses",
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "live", "stale": False, "message": None},
            "bosses": repository.get_bosses_payload(),
        },
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "fallback", "stale": True, "message": None},
            "bosses": [],
        },
    )


@api.get("/stats", response_model=StatsResponse)
def get_stats() -> dict[str, Any]:
    return cached_response(
        "stats",
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "live", "stale": False, "message": None},
            "stats": repository.get_stats_payload(),
        },
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "fallback", "stale": True, "message": None},
            "stats": {
                "current_weight": None,
                "current_weight_date": None,
                "total_workouts": 0,
                "workouts_last_30_days": 0,
                "current_week_streak": 0,
                "total_volume_kg": 0,
                "record_workout_date": None,
                "record_workout_volume_kg": None,
                "average_last_5_workouts_kg": 0,
            },
        },
    )


@api.get("/events", response_model=EventsResponse)
def get_events() -> dict[str, Any]:
    return cached_response(
        "events",
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "live", "stale": False, "message": None},
            "events": repository.get_events_payload(),
        },
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "fallback", "stale": True, "message": None},
            "events": [],
        },
    )


@api.get("/weight-chart", response_model=WeightChartResponse)
def get_weight_chart() -> dict[str, Any]:
    return cached_response(
        "weight_chart",
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "live", "stale": False, "message": None},
            "points": repository.get_weight_chart_payload(),
        },
        lambda: {
            "meta": {"updated_at": now_utc(), "source": "fallback", "stale": True, "message": None},
            "points": [],
        },
    )


app.include_router(api)


@app.get("/health")
def healthcheck() -> dict[str, Any]:
    health = repository.health_status()
    health["cache_entries"] = cache.size()
    health["status"] = "ok" if health["db"] == "ok" else "degraded"
    if health["db"] != "ok":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health)
    return health
