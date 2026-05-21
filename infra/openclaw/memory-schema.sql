-- OpenClaw personal secretary memory tables.
-- Intended database: jarvis_memory.
-- Keep writes limited to these assistant_* tables.

CREATE TABLE IF NOT EXISTS assistant_notes (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT NOT NULL DEFAULT 'telegram',
    category TEXT NOT NULL DEFAULT 'note',
    title TEXT,
    body TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS assistant_tasks (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    title TEXT NOT NULL,
    body TEXT,
    project TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    due_at TIMESTAMPTZ,
    priority TEXT NOT NULL DEFAULT 'normal',
    source TEXT NOT NULL DEFAULT 'telegram'
);

CREATE TABLE IF NOT EXISTS assistant_decisions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    topic TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT,
    source TEXT NOT NULL DEFAULT 'telegram',
    superseded_by BIGINT REFERENCES assistant_decisions(id)
);

CREATE TABLE IF NOT EXISTS assistant_reminders (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    remind_at TIMESTAMPTZ NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled',
    channel TEXT NOT NULL DEFAULT 'telegram',
    source TEXT NOT NULL DEFAULT 'telegram'
);

CREATE TABLE IF NOT EXISTS assistant_user_profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT NOT NULL DEFAULT 'manual'
);

CREATE INDEX IF NOT EXISTS assistant_notes_category_idx ON assistant_notes(category);
CREATE INDEX IF NOT EXISTS assistant_notes_tags_idx ON assistant_notes USING GIN(tags);
CREATE INDEX IF NOT EXISTS assistant_tasks_status_idx ON assistant_tasks(status);
CREATE INDEX IF NOT EXISTS assistant_tasks_due_at_idx ON assistant_tasks(due_at);
CREATE INDEX IF NOT EXISTS assistant_reminders_status_due_idx ON assistant_reminders(status, remind_at);

