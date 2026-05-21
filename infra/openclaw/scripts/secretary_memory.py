#!/usr/bin/env python3
"""Safe PostgreSQL access for OpenClaw secretary memory tables."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
from typing import Any


SSH_TARGET = os.environ.get("OPENCLAW_MEMORY_SSH_TARGET", "root@147.45.238.120")
SSH_PROXY_JUMP = os.environ.get("OPENCLAW_MEMORY_SSH_PROXY_JUMP", "")
POSTGRES_CONTAINER = os.environ.get("OPENCLAW_POSTGRES_CONTAINER", "postgres")
POSTGRES_USER = os.environ.get("OPENCLAW_POSTGRES_USER", "jarvis")
POSTGRES_DB = os.environ.get("OPENCLAW_POSTGRES_DB", "jarvis_memory")
QUERY_LIMIT = 20


def sql_json_literal(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False)
    delimiter = "json_" + secrets.token_hex(8)
    while delimiter in text:
        delimiter = "json_" + secrets.token_hex(8)
    return f"${delimiter}${text}${delimiter}$::jsonb"


def run_psql(sql: str) -> str:
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no"]
    if SSH_PROXY_JUMP:
        ssh_cmd.extend(["-J", SSH_PROXY_JUMP])
    ssh_cmd.append(SSH_TARGET)
    ssh_cmd.extend(
        [
            "docker",
            "exec",
            "-i",
            POSTGRES_CONTAINER,
            "psql",
            "-U",
            POSTGRES_USER,
            "-d",
            POSTGRES_DB,
            "-X",
            "-q",
            "-t",
            "-A",
        ]
    )
    result = subprocess.run(
        ssh_cmd,
        input=sql,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "psql command failed")
    return result.stdout.strip()


def parse_json_lines(raw: str) -> list[dict[str, Any]]:
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def save_note(payload: dict[str, Any]) -> dict[str, Any]:
    body = str(payload.get("body", "")).strip()
    if not body:
        raise ValueError("body is required")
    data = {
        "source": str(payload.get("source") or "telegram"),
        "category": str(payload.get("category") or "note"),
        "title": payload.get("title"),
        "body": body,
        "tags": payload.get("tags") or [],
    }
    sql = f"""
WITH payload AS (SELECT {sql_json_literal(data)} AS j),
inserted AS (
  INSERT INTO assistant_notes (source, category, title, body, tags)
  SELECT
    j->>'source',
    j->>'category',
    NULLIF(j->>'title', ''),
    j->>'body',
    COALESCE(ARRAY(SELECT jsonb_array_elements_text(j->'tags')), '{{}}'::text[])
  FROM payload
  RETURNING id, created_at, category, title, body, tags, status
)
SELECT row_to_json(inserted)::text FROM inserted;
"""
    return parse_json_lines(run_psql(sql))[0]


def save_task(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title", "")).strip()
    if not title:
        raise ValueError("title is required")
    data = {
        "title": title,
        "body": payload.get("body"),
        "project": payload.get("project"),
        "priority": str(payload.get("priority") or "normal"),
        "source": str(payload.get("source") or "telegram"),
    }
    sql = f"""
WITH payload AS (SELECT {sql_json_literal(data)} AS j),
inserted AS (
  INSERT INTO assistant_tasks (title, body, project, priority, source)
  SELECT
    j->>'title',
    NULLIF(j->>'body', ''),
    NULLIF(j->>'project', ''),
    j->>'priority',
    j->>'source'
  FROM payload
  RETURNING id, created_at, title, body, project, status, priority
)
SELECT row_to_json(inserted)::text FROM inserted;
"""
    return parse_json_lines(run_psql(sql))[0]


def save_decision(payload: dict[str, Any]) -> dict[str, Any]:
    topic = str(payload.get("topic", "")).strip()
    decision = str(payload.get("decision", "")).strip()
    if not topic or not decision:
        raise ValueError("topic and decision are required")
    data = {
        "topic": topic,
        "decision": decision,
        "reason": payload.get("reason"),
        "source": str(payload.get("source") or "telegram"),
    }
    sql = f"""
WITH payload AS (SELECT {sql_json_literal(data)} AS j),
inserted AS (
  INSERT INTO assistant_decisions (topic, decision, reason, source)
  SELECT
    j->>'topic',
    j->>'decision',
    NULLIF(j->>'reason', ''),
    j->>'source'
  FROM payload
  RETURNING id, created_at, topic, decision, reason
)
SELECT row_to_json(inserted)::text FROM inserted;
"""
    return parse_json_lines(run_psql(sql))[0]


def search_memory(payload: dict[str, Any]) -> dict[str, Any]:
    query = str(payload.get("query", "")).strip()
    if not query:
        raise ValueError("query is required")
    data = {"query": query, "limit": min(int(payload.get("limit") or 10), QUERY_LIMIT)}
    sql = f"""
WITH payload AS (SELECT {sql_json_literal(data)} AS j),
note_rows AS (
  SELECT 'note' AS type, id, created_at, title, body, category AS meta
  FROM assistant_notes, payload
  WHERE body ILIKE '%' || (j->>'query') || '%'
     OR title ILIKE '%' || (j->>'query') || '%'
     OR category ILIKE '%' || (j->>'query') || '%'
  ORDER BY created_at DESC
  LIMIT (SELECT (j->>'limit')::int FROM payload)
),
task_rows AS (
  SELECT 'task' AS type, id, created_at, title, COALESCE(body, '') AS body, status AS meta
  FROM assistant_tasks, payload
  WHERE title ILIKE '%' || (j->>'query') || '%'
     OR body ILIKE '%' || (j->>'query') || '%'
     OR project ILIKE '%' || (j->>'query') || '%'
  ORDER BY created_at DESC
  LIMIT (SELECT (j->>'limit')::int FROM payload)
),
decision_rows AS (
  SELECT 'decision' AS type, id, created_at, topic AS title, decision AS body, COALESCE(reason, '') AS meta
  FROM assistant_decisions, payload
  WHERE topic ILIKE '%' || (j->>'query') || '%'
     OR decision ILIKE '%' || (j->>'query') || '%'
     OR reason ILIKE '%' || (j->>'query') || '%'
  ORDER BY created_at DESC
  LIMIT (SELECT (j->>'limit')::int FROM payload)
),
rows AS (
  SELECT * FROM note_rows
  UNION ALL SELECT * FROM task_rows
  UNION ALL SELECT * FROM decision_rows
  ORDER BY created_at DESC
  LIMIT (SELECT (j->>'limit')::int FROM payload)
)
SELECT row_to_json(rows)::text FROM rows;
"""
    return {"query": query, "rows": parse_json_lines(run_psql(sql))}


def list_open_tasks(payload: dict[str, Any]) -> dict[str, Any]:
    project = str(payload.get("project") or "").strip()
    data = {"project": project, "limit": min(int(payload.get("limit") or 20), QUERY_LIMIT)}
    project_filter = "AND project ILIKE '%' || (j->>'project') || '%'" if project else ""
    sql = f"""
WITH payload AS (SELECT {sql_json_literal(data)} AS j),
rows AS (
  SELECT id, created_at, title, body, project, status, priority, due_at
  FROM assistant_tasks, payload
  WHERE status IN ('open', 'active', 'todo')
  {project_filter}
  ORDER BY created_at DESC
  LIMIT (SELECT (j->>'limit')::int FROM payload)
)
SELECT row_to_json(rows)::text FROM rows;
"""
    return {"project": project or None, "tasks": parse_json_lines(run_psql(sql))}


COMMANDS = {
    "save-note": save_note,
    "save-task": save_task,
    "save-decision": save_decision,
    "search-memory": search_memory,
    "open-tasks": list_open_tasks,
}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--json", default="{}")
    args = parser.parse_args()
    payload = json.loads(args.json)
    result = COMMANDS[args.command](payload)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
