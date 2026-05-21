#!/usr/bin/env python3
"""MCP server exposing safe secretary tools to OpenClaw."""

from __future__ import annotations

import secretary_context_search as context_search
import secretary_memory as memory
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("openclaw-secretary")


@mcp.tool()
def search_context(query: str, limit: int = 7) -> dict:
    """Read-only точечный поиск по Claude_Home: brain/, projects/, infra/, sessions/."""
    return context_search.search_context(query, None, limit)


@mcp.tool()
def project_status() -> dict:
    """Вернуть статусы и следующие шаги из brain/projects.md."""
    return context_search.list_project_status()


@mcp.tool()
def sync_context() -> dict:
    """Обновить checkout Claude_Home через git pull --ff-only."""
    return context_search.sync_context()


@mcp.tool()
def save_note(body: str, title: str | None = None, category: str = "note", tags: list[str] | None = None) -> dict:
    """Сохранить простую заметку в assistant_notes."""
    return memory.save_note({"body": body, "title": title, "category": category, "tags": tags or []})


@mcp.tool()
def save_task(
    title: str,
    body: str | None = None,
    project: str | None = None,
    priority: str = "normal",
) -> dict:
    """Сохранить задачу в assistant_tasks."""
    return memory.save_task({"title": title, "body": body, "project": project, "priority": priority})


@mcp.tool()
def save_decision(topic: str, decision: str, reason: str | None = None) -> dict:
    """Сохранить решение в assistant_decisions."""
    return memory.save_decision({"topic": topic, "decision": decision, "reason": reason})


@mcp.tool()
def search_memory(query: str, limit: int = 10) -> dict:
    """Найти заметки, задачи и решения в assistant_*."""
    return memory.search_memory({"query": query, "limit": limit})


@mcp.tool()
def open_tasks(project: str | None = None, limit: int = 20) -> dict:
    """Показать открытые задачи из assistant_tasks."""
    return memory.list_open_tasks({"project": project, "limit": limit})


if __name__ == "__main__":
    mcp.run()
