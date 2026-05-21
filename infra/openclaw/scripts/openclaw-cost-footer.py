#!/usr/bin/env python3
"""
Read an OpenClaw session JSONL file and print a compact RUB cost footer.

OpenClaw session messages already contain usage.cost.total in USD when the
provider reports usage. This script is intentionally dumb and cheap: no model,
no internet, no guessing.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


DEFAULT_USD_RUB = 90.0


def read_usd_rub() -> float:
    raw = os.environ.get("USD_RUB_RATE", "").strip()
    if not raw:
        return DEFAULT_USD_RUB
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        return DEFAULT_USD_RUB


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def latest_usd_cost(path: Path) -> float | None:
    latest: float | None = None
    for event in iter_jsonl(path):
        if event.get("type") != "message":
            continue
        message = event.get("message") or {}
        if message.get("role") != "assistant":
            continue
        usage = message.get("usage") or {}
        cost = usage.get("cost") or {}
        total = cost.get("total")
        if isinstance(total, (int, float)):
            latest = float(total)
    return latest


def format_footer(usd: float, usd_rub: float) -> str:
    rub = usd * usd_rub
    if rub < 0.5:
        return "(<1 ₽)"
    if rub < 10:
        return f"(≈{rub:.1f} ₽)"
    return f"(≈{rub:.0f} ₽)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("session_jsonl", type=Path)
    parser.add_argument("--usd-rub", type=float, default=None)
    args = parser.parse_args()

    usd = latest_usd_cost(args.session_jsonl)
    if usd is None:
        print("(стоимость: нет данных)")
        return 2

    print(format_footer(usd, args.usd_rub or read_usd_rub()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

