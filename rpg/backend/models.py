from pydantic import BaseModel
from typing import Optional
import datetime


class HeroStats(BaseModel):
    name: str
    class_name: str
    level: int
    level_name: str
    workouts_count: int
    next_level_threshold: int
    prev_level_threshold: int
    strength: float
    endurance: float
    recovery: float
    volume: float


class Quest(BaseModel):
    id: str
    icon: str
    name: str
    description: str
    status: str  # active / completed / locked
    progress: float  # 0.0 - 1.0
    progress_text: str


class Boss(BaseModel):
    name: str
    icon: str
    target_weight: float
    status: str  # defeated / active / locked
    current_weight: float
    progress: float  # 0.0 - 1.0


class StatCard(BaseModel):
    current_weight: Optional[float] = None
    current_body_fat: Optional[float] = None
    total_workouts: int = 0
    workouts_30d: int = 0
    total_volume: float = 0.0
    best_workout: Optional[dict] = None
    avg_volume_5: Optional[float] = None
    current_streak_weeks: int = 0


class Event(BaseModel):
    date_str: str
    icon: str
    text: str


class WeightPoint(BaseModel):
    date: str
    weight: float
