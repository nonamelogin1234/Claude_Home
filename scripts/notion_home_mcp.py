#!/usr/bin/env python3
"""Opinionated Notion MCP entrypoint for the personal workspace."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from mcp.server.fastmcp import FastMCP


DEFAULT_ROOT_PAGE_ID = "36ea682f-4234-801c-8396-c21a0bf1b5de"
NOTION_VERSION = os.environ.get("NOTION_VERSION", "2026-03-11")
ROOT_PAGE_ID = os.environ.get("NOTION_ROOT_PAGE_ID", DEFAULT_ROOT_PAGE_ID)

mcp = FastMCP("notion-home")


class NotionError(RuntimeError):
    pass


def _token() -> str:
    token = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")
    if not token:
        raise NotionError(
            "NOTION_API_KEY is not set. Create a Notion internal integration, "
            "share the root page with it, then set the user environment variable."
        )
    return token


def _normalize_id(value: str) -> str:
    value = value.strip()
    if "notion.so" in value:
        match = re.search(r"([0-9a-fA-F]{32})(?:[?#/]|$)", value)
        if match:
            value = match.group(1)
    value = value.replace("-", "")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", value):
        raise NotionError(f"Invalid Notion id or URL: {value}")
    return f"{value[0:8]}-{value[8:12]}-{value[12:16]}-{value[16:20]}-{value[20:32]}".lower()


def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.notion.com/v1{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise NotionError(f"Notion API HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise NotionError(f"Notion API connection failed: {exc.reason}") from exc


def _rich_text(items: list[dict[str, Any]] | None) -> str:
    if not items:
        return ""
    return "".join(item.get("plain_text", "") for item in items)


def _title_from_page(page: dict[str, Any]) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return _rich_text(prop.get("title")) or "Untitled"
    return "Untitled"


def _page_summary(page_id: str) -> dict[str, Any]:
    page = _request("GET", f"/pages/{_normalize_id(page_id)}")
    return {
        "id": page["id"],
        "title": _title_from_page(page),
        "url": page.get("url"),
        "last_edited_time": page.get("last_edited_time"),
        "archived": page.get("archived", False) or page.get("in_trash", False),
    }


def _children(block_id: str) -> list[dict[str, Any]]:
    block_id = _normalize_id(block_id)
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        query = f"?start_cursor={urllib.parse.quote(cursor)}" if cursor else ""
        data = _request("GET", f"/blocks/{block_id}/children{query}")
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            return results
        cursor = data.get("next_cursor")


def _block_title(block: dict[str, Any]) -> str:
    block_type = block.get("type")
    if block_type == "child_page":
        return block.get("child_page", {}).get("title", "Untitled")
    if block_type == "child_database":
        return block.get("child_database", {}).get("title", "Untitled database")
    data = block.get(block_type or "", {})
    return _rich_text(data.get("rich_text")) or _rich_text(data.get("title"))


def _block_to_text(block: dict[str, Any], indent: int = 0) -> list[str]:
    prefix = "  " * indent
    block_type = block.get("type")
    data = block.get(block_type or "", {})
    text = _rich_text(data.get("rich_text"))

    if block_type == "paragraph":
        return [prefix + text] if text else []
    if block_type in {"heading_1", "heading_2", "heading_3"}:
        level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[block_type]
        return [f"{prefix}{level} {text}".rstrip()]
    if block_type == "bulleted_list_item":
        return [f"{prefix}- {text}".rstrip()]
    if block_type == "numbered_list_item":
        return [f"{prefix}1. {text}".rstrip()]
    if block_type == "to_do":
        checked = "x" if data.get("checked") else " "
        return [f"{prefix}- [{checked}] {text}".rstrip()]
    if block_type == "quote":
        return [f"{prefix}> {text}".rstrip()]
    if block_type == "code":
        language = data.get("language") or ""
        return [f"{prefix}```{language}", text, f"{prefix}```"]
    if block_type == "child_page":
        return [f"{prefix}[[{_block_title(block)}]] ({block.get('id')})"]
    if block_type == "child_database":
        return [f"{prefix}[database] {_block_title(block)} ({block.get('id')})"]
    if block_type == "table_row":
        cells = ["".join(cell.get("plain_text", "") for cell in rich) for rich in data.get("cells", [])]
        return [prefix + " | ".join(cells)]
    if text:
        return [f"{prefix}{text}"]
    return []


def _page_content(page_id: str, include_child_blocks: bool = True) -> dict[str, Any]:
    page = _page_summary(page_id)
    lines: list[str] = []
    linked_pages: list[dict[str, Any]] = []
    linked_databases: list[dict[str, Any]] = []

    for block in _children(page["id"]):
        block_type = block.get("type")
        if block_type == "child_page":
            linked_pages.append({"id": block["id"], "title": _block_title(block)})
        elif block_type == "child_database":
            linked_databases.append({"id": block["id"], "title": _block_title(block)})
        lines.extend(_block_to_text(block))
        if include_child_blocks and block.get("has_children") and block_type not in {"child_page", "child_database"}:
            for child in _children(block["id"]):
                lines.extend(_block_to_text(child, indent=1))

    return {
        **page,
        "content": "\n".join(line for line in lines if line is not None).strip(),
        "linked_pages": linked_pages,
        "linked_databases": linked_databases,
    }


def _tree(page_id: str, depth: int, seen: set[str] | None = None) -> dict[str, Any]:
    seen = seen or set()
    page = _page_summary(page_id)
    if page["id"] in seen:
        return {**page, "children": [], "cycle": True}
    seen.add(page["id"])

    node = {**page, "children": []}
    if depth <= 0:
        return node

    for block in _children(page["id"]):
        if block.get("type") == "child_page":
            node["children"].append(_tree(block["id"], depth - 1, seen))
        elif block.get("type") == "child_database":
            node["children"].append(
                {
                    "id": block["id"],
                    "title": _block_title(block),
                    "type": "database",
                    "children": [],
                }
            )
    return node


def _flatten_tree(node: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "id": node.get("id"),
            "title": node.get("title"),
            "url": node.get("url"),
            "type": node.get("type", "page"),
        }
    ]
    for child in node.get("children", []):
        rows.extend(_flatten_tree(child))
    return rows


@mcp.tool()
def fetch_home() -> dict[str, Any]:
    """Read the configured Notion home page and return its direct content and links."""
    try:
        return _page_content(ROOT_PAGE_ID)
    except NotionError as exc:
        return {"ok": False, "error": str(exc), "root_page_id": ROOT_PAGE_ID}


@mcp.tool()
def list_tree(max_depth: int = 3) -> dict[str, Any]:
    """List the page tree under the configured Notion home page."""
    try:
        max_depth = max(0, min(int(max_depth), 6))
        tree = _tree(ROOT_PAGE_ID, max_depth)
        return {"ok": True, "root_page_id": ROOT_PAGE_ID, "tree": tree, "pages": _flatten_tree(tree)}
    except NotionError as exc:
        return {"ok": False, "error": str(exc), "root_page_id": ROOT_PAGE_ID}


@mcp.tool()
def fetch_page(page_id_or_url: str) -> dict[str, Any]:
    """Fetch a Notion page by id or URL and render its content as readable text."""
    try:
        return {"ok": True, "page": _page_content(page_id_or_url)}
    except NotionError as exc:
        return {"ok": False, "error": str(exc)}


@mcp.tool()
def fetch_page_by_title(title: str, max_depth: int = 4) -> dict[str, Any]:
    """Find a page under Notion home by title, then fetch it."""
    try:
        needle = title.strip().casefold()
        tree = _tree(ROOT_PAGE_ID, max(0, min(int(max_depth), 6)))
        matches = [page for page in _flatten_tree(tree) if needle in (page.get("title") or "").casefold()]
        if not matches:
            return {"ok": False, "error": f"No page under Notion home matched title: {title}", "matches": []}
        exact = [page for page in matches if (page.get("title") or "").casefold() == needle]
        page = exact[0] if exact else matches[0]
        return {"ok": True, "match": page, "page": _page_content(page["id"])}
    except NotionError as exc:
        return {"ok": False, "error": str(exc)}


@mcp.tool()
def search_known_pages(query: str, max_depth: int = 5) -> dict[str, Any]:
    """Search titles of pages reachable from Notion home. This is deterministic tree search, not global Notion search."""
    try:
        needle = query.strip().casefold()
        tree = _tree(ROOT_PAGE_ID, max(0, min(int(max_depth), 6)))
        matches = [
            page for page in _flatten_tree(tree)
            if needle in (page.get("title") or "").casefold()
        ]
        return {"ok": True, "query": query, "matches": matches}
    except NotionError as exc:
        return {"ok": False, "error": str(exc)}


if __name__ == "__main__":
    mcp.run()
