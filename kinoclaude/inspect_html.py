import re

path = r'C:/Users/user/Documents/Claude_Home/kinoclaude/Профиль_ jesusmaan - Оценки.html'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    html = f.read()

# Смотрим последние 20KB
tail = html[-20000:]
print("=== LAST 20KB scripts with data ===")
scripts_in_tail = re.findall(r'<script[^>]*>(.*?)</script>', tail, re.DOTALL)
print(f"Scripts in tail: {len(scripts_in_tail)}")
for i, s in enumerate(scripts_in_tail):
    s = s.strip()
    if len(s) > 50:
        print(f"\n--- Script {i} (len={len(s)}) ---")
        print(s[:500])

# Ищем числа 1-10 в форматте "361:8" или "361,8" или похожих паттернах
rating_pairs = re.findall(r'(\d{3,7})[,:\s]+([1-9]|10)\b', html)
# Фильтруем — только если первое число похоже на film_id (>100)
valid_pairs = [(a, b) for a, b in rating_pairs if int(a) > 100 and int(b) <= 10]
print(f"\nPotential id:rating pairs: {len(valid_pairs)}")
print(f"Sample: {valid_pairs[:10]}")
