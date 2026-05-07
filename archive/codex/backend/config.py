from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "postgres"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "jarvis_memory"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "jarvis"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", ""))
    hero_name: str = field(default_factory=lambda: os.getenv("HERO_NAME", "Сергей"))
    hero_class: str = field(default_factory=lambda: os.getenv("HERO_CLASS", "Воин — Путь Трансформации"))
    cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300")))
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:8088,https://mcp.myserver-ai.ru")
        )
    )


LEVELS = [
    (1, 1, 10, "Новобранец", "Воин"),
    (2, 11, 25, "Воин", "Ветеран"),
    (3, 26, 50, "Ветеран", "Чемпион"),
    (4, 51, 100, "Чемпион", "Легенда"),
    (5, 101, None, "Легенда", None),
]

BOSSES = [
    ("gatekeeper", "🛡️", "Страж Порога", 110.0),
    ("plateau_keeper", "⛰️", "Хранитель Плато", 105.0),
    ("hundred_dragon", "🐉", "Дракон Сотни", 99.0),
    ("shadow_lord", "🌘", "Теневой Лорд", 90.0),
    ("final_boss", "👑", "Финальный Босс", 85.0),
]
