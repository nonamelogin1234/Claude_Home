from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Settings


logger = logging.getLogger(__name__)


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @contextmanager
    def connection(self) -> Iterator[Any]:
        logger.debug("Opening PostgreSQL connection to %s:%s/%s", self.settings.db_host, self.settings.db_port, self.settings.db_name)
        conn = psycopg2.connect(
            host=self.settings.db_host,
            port=self.settings.db_port,
            dbname=self.settings.db_name,
            user=self.settings.db_user,
            password=self.settings.db_password,
            cursor_factory=RealDictCursor,
        )
        try:
            yield conn
        finally:
            conn.close()

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row is None:
                    logger.debug("Query returned no rows")
                    return None
                return dict(row)

    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def ping(self) -> bool:
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            logger.exception("Database ping failed")
            return False
