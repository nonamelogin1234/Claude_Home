#!/usr/bin/env python3
"""Read-only search over the allowed Claude_Home context directories."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONTEXT_ROOT = Path(os.environ.get("OPENCLAW_CONTEXT_ROOT", "/home/sergei/Claude_Home"))
ALLOWED_DIRS = ("brain", "projects", "infra", "sessions")
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".sql",
    ".py",
}
MAX_FILE_BYTES = 512_000
MAX_SNIPPET_CHARS = 900


@dataclass
class Match:
    path: str
    line: int
    score: int
    snippet: str


def resolve_context_root(value: str | None) -> Path:
    root = Path(value).expanduser().resolve() if value else DEFAULT_CONTEXT_ROOT.resolve()
    if not root.exists():
        raise SystemExit(f"Context root not found: {root}")
    return root


def iter_allowed_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirname in ALLOWED_DIRS:
        base = (root / dirname).resolve()
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if ".git" in path.parts:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            files.append(path)
    return files


def tokenize(query: str) -> list[str]:
    return [part.lower() for part in re.findall(r"[\wа-яА-ЯёЁ-]{2,}", query)]


def build_snippet(lines: list[str], index: int) -> str:
    start = max(0, index - 2)
    end = min(len(lines), index + 3)
    snippet = "\n".join(line.rstrip() for line in lines[start:end]).strip()
    if len(snippet) > MAX_SNIPPET_CHARS:
        return snippet[: MAX_SNIPPET_CHARS - 1].rstrip() + "…"
    return snippet


def search_context(query: str, context_root: str | None = None, limit: int = 7) -> dict:
    root = resolve_context_root(context_root)
    terms = tokenize(query)
    if not terms:
        raise SystemExit("Search query is empty")

    matches: list[Match] = []
    for path in iter_allowed_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lower_lines = text.lower().splitlines()
        original_lines = text.splitlines()
        rel_path = path.relative_to(root).as_posix()

        for index, line in enumerate(lower_lines):
            hits = sum(1 for term in terms if term in line)
            if hits == 0:
                continue
            title_bonus = 3 if original_lines[index].lstrip().startswith("#") else 0
            exact_bonus = 4 if query.lower() in line else 0
            path_bonus = sum(2 for term in terms if term in rel_path.lower())
            score = hits * 5 + title_bonus + exact_bonus + path_bonus
            matches.append(
                Match(
                    path=rel_path,
                    line=index + 1,
                    score=score,
                    snippet=build_snippet(original_lines, index),
                )
            )

    matches.sort(key=lambda item: (-item.score, item.path, item.line))
    selected = matches[: max(1, min(limit, 20))]
    return {
        "query": query,
        "context_root": str(root),
        "matches": [item.__dict__ for item in selected],
    }


def list_project_status(context_root: str | None = None) -> dict:
    root = resolve_context_root(context_root)
    projects_file = root / "brain" / "projects.md"
    if not projects_file.exists():
        raise SystemExit(f"Missing projects file: {projects_file}")

    lines = projects_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    rows = []
    in_project_tables = False
    for line in lines:
        if line.startswith("## Код-проекты") or line.startswith("## Инфраструктура"):
            in_project_tables = True
            continue
        if line.startswith("## В архиве") or line.startswith("## Сервисы без папки"):
            in_project_tables = False
            continue
        if not in_project_tables:
            continue
        if not line.startswith("|") or "---" in line or "Проект" in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        project, status, next_step, folder = parts[:4]
        rows.append(
            {
                "project": project,
                "status": status,
                "next_step": next_step,
                "folder": folder,
            }
        )
    return {"source": "brain/projects.md", "projects": rows}


def sync_context(context_root: str | None = None) -> dict:
    root = resolve_context_root(context_root)
    if not (root / ".git").exists():
        raise SystemExit(f"Context root is not a git checkout: {root}")

    result = subprocess.run(
        ["git", "-C", str(root), "pull", "--ff-only"],
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    return {
        "context_root": str(root),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("search", "projects", "sync"))
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--context-root", default=None)
    parser.add_argument("--limit", type=int, default=7)
    args = parser.parse_args()

    if args.command == "search":
        payload = search_context(args.query, args.context_root, args.limit)
    elif args.command == "projects":
        payload = list_project_status(args.context_root)
    else:
        payload = sync_context(args.context_root)

    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
