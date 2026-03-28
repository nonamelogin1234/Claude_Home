import urllib.request
import json
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def shell(cmd):
    payload = json.dumps({"cmd": cmd}).encode()
    req = urllib.request.Request(
        "https://mcp.myserver-ai.ru:7723",
        data=payload,
        headers={"X-Secret": "shell-api-secret-2026", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return json.loads(resp.read())

# Статус сервиса
r = shell("systemctl is-active kinoclaude")
print("service active:", r['stdout'].strip())

# Статус обогащения
r2 = shell("docker exec postgres psql -U jarvis -d jarvis_memory -c \"SELECT COUNT(*) as total, COUNT(enriched_at) as enriched FROM kinoclaude_ratings;\"")
print("DB stats:", r2['stdout'])

# Проверяем лог обогащения
r3 = shell("tail -3 /tmp/enrich.log 2>/dev/null || echo 'no log'")
print("enrich log:", r3['stdout'])
