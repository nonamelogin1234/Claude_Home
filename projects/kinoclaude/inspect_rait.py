import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:/Users/user/Documents/Claude_Home/kinoclaude/rait_new.txt', 'r', encoding='cp1251') as f:
    lines = [l.rstrip('\n').strip() for l in f.readlines()]

# Якорь: строки с датой "DD.MM.YYYY, HH:MM"
date_pat = re.compile(r'^\d{2}\.\d{2}\.\d{4},\s*\d{2}:\d{2}$')
date_indices = [i for i, l in enumerate(lines) if date_pat.match(l)]
print(f"Date lines found: {len(date_indices)}")

# Структура вокруг даты: дата [i], оценка [i+1]
# Назад от даты ищем: row_num, ru_title, [en_title], kp_line
records = []
for idx in date_indices:
    date_str = lines[idx]
    rating_str = lines[idx+1] if idx+1 < len(lines) else ''
    
    # Назад ищем блок этого фильма
    # kp_line: содержит "(число)" и "мин" ИЛИ только "число"
    # ru_title: содержит "(ГГГГ)"
    # Ищем RU title — максимум 4 строки назад
    ru_title = None
    en_title = None
    kp_line = None
    
    for back in range(1, 6):
        l = lines[idx - back] if idx - back >= 0 else ''
        if re.search(r'\(\d{4}\)', l):  # год в скобках → RU title
            ru_title = l
            # EN title может быть между ru_title и kp_line
            if back > 2:
                candidate = lines[idx - back + 1]
                if candidate and '\xa0' not in candidate and not re.search(r'\d{4}', candidate[:4]):
                    en_title = candidate
            break
    
    records.append({
        'ru_title': ru_title,
        'en_title': en_title,
        'date': date_str,
        'rating': rating_str,
    })

print(f"Records parsed: {len(records)}")
print("\n=== First 10 records ===")
for r in records[:10]:
    print(r)

# Статистика оценок
ratings = [r['rating'] for r in records if r['rating'].isdigit()]
print(f"\nRatings found: {len(ratings)}")
from collections import Counter
print(f"Distribution: {sorted(Counter(ratings).items())}")

# Сколько пустых оценок
empty = [r for r in records if not r['rating'].isdigit()]
print(f"Empty/invalid ratings: {len(empty)}")
if empty:
    print("Sample empty:", empty[:5])
