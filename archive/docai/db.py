"""
DocAI -- база данных (SQLite).
Все данные хранятся в %APPDATA%/DocAI/.
"""

import sqlite3
import os
import hashlib
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# ─── Пути ────────────────────────────────────────────────────────────────────

APP_DIR = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'DocAI'
DB_PATH = APP_DIR / 'docai.db'
DATA_DIR = APP_DIR / 'data'
MODELS_DIR = APP_DIR / 'models'


def ensure_dirs():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    MODELS_DIR.mkdir(exist_ok=True)


def file_data_dir(file_id: int) -> Path:
    """Возвращает директорию для данных файла, создаёт если нет."""
    d = DATA_DIR / str(file_id)
    d.mkdir(exist_ok=True)
    return d


# ─── Соединение ───────────────────────────────────────────────────────────────

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ─── Инициализация ────────────────────────────────────────────────────────────

def init_db():
    ensure_dirs()
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS files (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            display_name TEXT NOT NULL,
            pdf_path    TEXT NOT NULL,
            status      TEXT DEFAULT 'pending',
            file_hash   TEXT,
            processed_at TEXT,
            error_msg   TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        """)


# ─── Проекты ──────────────────────────────────────────────────────────────────

def create_project(name: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        return cur.lastrowid


def rename_project(project_id: int, new_name: str):
    with get_conn() as conn:
        conn.execute("UPDATE projects SET name=? WHERE id=?", (new_name, project_id))


def delete_project(project_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))


def get_projects() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
        return [dict(r) for r in rows]


# ─── Файлы ────────────────────────────────────────────────────────────────────

def add_file(project_id: int, display_name: str, pdf_path: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO files (project_id, display_name, pdf_path) VALUES (?,?,?)",
            (project_id, display_name, pdf_path)
        )
        return cur.lastrowid


def remove_file(file_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM files WHERE id=?", (file_id,))


def move_file(file_id: int, new_project_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE files SET project_id=? WHERE id=?", (new_project_id, file_id))


def update_file_status(file_id: int, status: str,
                        file_hash: str = None, error_msg: str = None):
    with get_conn() as conn:
        now = datetime.now().isoformat() if status in ('ready', 'error') else None
        conn.execute(
            """UPDATE files
               SET status=?, file_hash=COALESCE(?,file_hash),
                   error_msg=?, processed_at=COALESCE(?,processed_at)
               WHERE id=?""",
            (status, file_hash, error_msg, now, file_id)
        )


def get_files(project_id: int = None) -> list[dict]:
    with get_conn() as conn:
        if project_id is not None:
            rows = conn.execute(
                "SELECT * FROM files WHERE project_id=? ORDER BY display_name",
                (project_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM files ORDER BY display_name").fetchall()
        return [dict(r) for r in rows]


def get_file(file_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
        return dict(row) if row else None


def pdf_hash(pdf_path: str) -> str:
    """MD5 первых 2MB PDF (быстро, достаточно для детекции изменений)."""
    h = hashlib.md5()
    with open(pdf_path, 'rb') as f:
        h.update(f.read(2 * 1024 * 1024))
    return h.hexdigest()


def file_needs_reindex(file_id: int) -> bool:
    """True если файл ещё не обработан или PDF изменился."""
    f = get_file(file_id)
    if not f or f['status'] != 'ready':
        return True
    try:
        current_hash = pdf_hash(f['pdf_path'])
        return current_hash != f['file_hash']
    except Exception:
        return True


# ─── Настройки ────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = '') -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row else default


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
            (key, value)
        )
