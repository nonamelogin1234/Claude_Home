from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ResponseMeta(BaseModel):
    updated_at: datetime
    source: Literal["live", "stale_cache", "fallback"]
    stale: bool = False
    message: str | None = None


class HeroStat(BaseModel):
    name: str
    value: float
    display_value: str
    unit: str


class HeroInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    name: str
    hero_class: str = Field(alias="class")
    level: int
    rank_title: str
    total_workouts: int
    progress_percent: float
    workouts_to_next_level: int
    next_rank_title: str | None = None
    last_workout_date: date | None = None
    stats: list[HeroStat]


class HeroResponse(BaseModel):
    meta: ResponseMeta
    hero: HeroInfo


class QuestItem(BaseModel):
    slug: str
    icon: str
    title: str
    description: str
    status: Literal["active", "completed", "locked"]
    progress_percent: float
    progress_label: str
    category: Literal["active", "archive"]


class QuestsResponse(BaseModel):
    meta: ResponseMeta
    quests: list[QuestItem]


class BossItem(BaseModel):
    slug: str
    icon: str
    title: str
    target_weight: float
    current_weight: float | None = None
    status: Literal["active", "completed", "locked"]
    progress_percent: float
    subtitle: str


class BossesResponse(BaseModel):
    meta: ResponseMeta
    bosses: list[BossItem]


class StatsPayload(BaseModel):
    current_weight: float | None = None
    current_weight_date: date | None = None
    total_workouts: int
    workouts_last_30_days: int
    current_week_streak: int
    total_volume_kg: float
    record_workout_date: date | None = None
    record_workout_volume_kg: float | None = None
    average_last_5_workouts_kg: float


class StatsResponse(BaseModel):
    meta: ResponseMeta
    stats: StatsPayload


class EventItem(BaseModel):
    date: date
    icon: str
    title: str
    description: str
    category: Literal["workout", "weight", "sleep", "record"]


class EventsResponse(BaseModel):
    meta: ResponseMeta
    events: list[EventItem]


class WeightPoint(BaseModel):
    date: date
    weight: float


class WeightChartResponse(BaseModel):
    meta: ResponseMeta
    points: list[WeightPoint]
