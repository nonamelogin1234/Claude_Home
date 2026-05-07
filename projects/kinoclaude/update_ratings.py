import sys, urllib.request, json, ssl
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

# Топ-10 по оценке для профиля
r = shell("""docker exec postgres psql -U jarvis -d jarvis_memory -c "
SELECT my_rating::int, title_ru, title, year
FROM kinoclaude_ratings
WHERE my_rating >= 9
ORDER BY my_rating DESC, date_watched DESC
LIMIT 30;" """)
print("=== Оценка 9-10 ===")
print(r['stdout'])

# Жанровая статистика (для обогащённых)
r2 = shell("""docker exec postgres psql -U jarvis -d jarvis_memory -c "
SELECT unnest(genres) as genre, COUNT(*) as cnt,
       ROUND(AVG(my_rating),2) as avg_rating
FROM kinoclaude_ratings
WHERE genres IS NOT NULL AND my_rating IS NOT NULL
GROUP BY genre ORDER BY cnt DESC LIMIT 20;" """)
print("=== Жанры ===")
print(r2['stdout'])

# Средняя оценка по жанрам
r3 = shell("""docker exec postgres psql -U jarvis -d jarvis_memory -c "
SELECT my_rating::int, COUNT(*) FROM kinoclaude_ratings
GROUP BY my_rating ORDER BY my_rating;" """)
print("=== Распределение оценок ===")
print(r3['stdout'])
