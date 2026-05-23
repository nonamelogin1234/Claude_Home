#!/usr/bin/env python3
"""Minimal MCP server for running commands with Vaultwarden secrets.

The server never returns secret values to the model. It only:
- reports Bitwarden CLI status;
- checks that an exact item exists;
- runs a command with one exact-item secret injected as an env var.

It intentionally does not list vault items.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "2024-11-05"
DEFAULT_BW_EXE = (
    r"C:\Users\no-na\AppData\Local\Microsoft\WinGet\Packages"
    r"\Bitwarden.CLI_Microsoft.Winget.Source_8wekyb3d8bbwe\bw.exe"
)


def respond(message_id: Any, result: Any = None, error: Any = None) -> None:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def content(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def bw_exe() -> str:
    configured = os.environ.get("BW_EXE")
    if configured:
        return configured
    return DEFAULT_BW_EXE if Path(DEFAULT_BW_EXE).exists() else "bw"


def run_bw(args: list[str], *, include_session: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if not include_session:
        env.pop("BW_SESSION", None)
    return subprocess.run(
        [bw_exe(), *args],
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def bw_status() -> dict[str, Any]:
    proc = run_bw(["status"])
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr.strip() or proc.stdout.strip()}
    data = json.loads(proc.stdout)
    return {
        "ok": True,
        "serverUrl": data.get("serverUrl"),
        "userEmail": data.get("userEmail"),
        "status": data.get("status"),
        "lastSync": data.get("lastSync"),
        "hasSessionEnv": bool(os.environ.get("BW_SESSION")),
    }


def extract_secret(item: dict[str, Any], field: str) -> str:
    if field == "password":
        value = item.get("login", {}).get("password")
    else:
        value = None
        for custom in item.get("fields") or []:
            if custom.get("name") == field:
                value = custom.get("value")
                break
    if not value:
        raise ValueError(f"Secret field is empty or missing: {field}")
    return str(value)


def get_secret(item_name: str, field: str = "password") -> str:
    if not item_name.strip():
        raise ValueError("itemName is required")
    proc = run_bw(["get", "item", item_name])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    item = json.loads(proc.stdout)
    return extract_secret(item, field)


def redact(text: str, secret: str) -> str:
    if not secret:
        return text
    return text.replace(secret, "[REDACTED_SECRET]")


def tool_status(_args: dict[str, Any]) -> dict[str, Any]:
    status = bw_status()
    return content(json.dumps({
        "bitwarden": status,
        "mode": "exact item lookup only; vault listing is disabled",
    }, ensure_ascii=False, indent=2))


def tool_check_secret(args: dict[str, Any]) -> dict[str, Any]:
    item_name = str(args.get("itemName") or args.get("alias") or "")
    field = str(args.get("field", "password"))
    secret = get_secret(item_name, field)
    return content(json.dumps({
        "item": item_name,
        "field": field,
        "found": True,
        "length": len(secret),
        "prefix": secret[:7] if len(secret) >= 7 else "",
    }, ensure_ascii=False, indent=2))


def tool_run_with_secret(args: dict[str, Any]) -> dict[str, Any]:
    item_name = str(args.get("itemName") or args.get("alias") or "")
    field = str(args.get("field", "password"))
    env_name = str(args.get("envName", "OPENAI_API_KEY"))
    command = args.get("command")
    cwd = args.get("cwd") or os.getcwd()

    if not isinstance(command, list) or not command:
        raise ValueError("command must be a non-empty array")
    command = [str(part) for part in command]

    secret = get_secret(item_name, field)

    env = os.environ.copy()
    env[env_name] = secret
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=int(args.get("timeoutSec", 3600)),
    )
    return content(json.dumps({
        "item": item_name,
        "field": field,
        "envName": env_name,
        "exitCode": proc.returncode,
        "stdout": redact(proc.stdout, secret),
        "stderr": redact(proc.stderr, secret),
    }, ensure_ascii=False, indent=2))


TOOLS = {
    "vaultwarden_status": {
        "handler": tool_status,
        "description": "Show Vaultwarden/Bitwarden CLI status and allowlisted secret aliases. Does not reveal secrets.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "vaultwarden_check_secret": {
        "handler": tool_check_secret,
        "description": "Check that an exact Vaultwarden item secret exists. Returns metadata only, never the secret value. Does not list the vault.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "itemName": {"type": "string"},
                "field": {"type": "string"},
                "alias": {"type": "string", "description": "Backward-compatible alias for itemName."},
            },
        },
    },
    "vaultwarden_run_with_secret": {
        "handler": tool_run_with_secret,
        "description": "Run a command with an exact Vaultwarden item secret injected as an environment variable. Secret is redacted from output. Does not list the vault.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "itemName": {"type": "string"},
                "field": {"type": "string"},
                "alias": {"type": "string", "description": "Backward-compatible alias for itemName."},
                "envName": {"type": "string"},
                "command": {"type": "array", "items": {"type": "string"}},
                "cwd": {"type": "string"},
                "timeoutSec": {"type": "integer"},
            },
            "required": ["command"],
        },
    },
}


def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            }
            for name, spec in TOOLS.items()
        ]
    }


def handle(message: dict[str, Any]) -> None:
    method = message.get("method")
    message_id = message.get("id")
    try:
        if method == "initialize":
            respond(message_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "vaultwarden-secrets", "version": "0.1.0"},
            })
        elif method == "tools/list":
            respond(message_id, list_tools())
        elif method == "tools/call":
            params = message.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            if name not in TOOLS:
                raise KeyError(f"Unknown tool: {name}")
            respond(message_id, TOOLS[name]["handler"](args))
        elif message_id is not None:
            respond(message_id, {})
    except Exception as exc:
        respond(message_id, error={"code": -32000, "message": str(exc)})


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            handle(json.loads(line))
        except Exception as exc:
            respond(None, error={"code": -32700, "message": str(exc)})


if __name__ == "__main__":
    main()
