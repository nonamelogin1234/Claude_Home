import urllib.request, json, ssl, base64

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

with open(r"C:\Users\user\Documents\Claude_Home\kinoclaude\profile.md", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

r = shell(f"echo '{b64}' | base64 -d > /opt/kinoclaude/profile.md && echo 'ok'")
print("profile.md:", r['stdout'].strip())
