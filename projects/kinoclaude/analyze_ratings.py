import sys
import re

with open('C:/Users/user/Documents/Claude_Home/kinoclaude/kinoclaude_ratings.md', 'r', encoding='utf-16') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')
print()

# Analyze structure
sample = []
for l in lines[:10]:
    cols = l.strip().split('\t')
    sample.append(cols)
    print(f'{len(cols)} cols: {cols[0]} | {cols[1][:40]} | {cols[-1][:30]}')

print()
print('--- Last 5 lines ---')
for l in lines[-5:]:
    cols = l.strip().split('\t')
    print(f'{len(cols)} cols: {cols[0]} | {cols[1][:40]} | {cols[-1][:30]}')

# Count film vs series
films = sum(1 for l in lines if '/film/' in l)
series = sum(1 for l in lines if '/series/' in l)
print(f'\nFilms: {films}, Series: {series}')

# Extract IDs
ids = []
for l in lines:
    m = re.search(r'/(film|series)/(\d+)/', l)
    if m:
        ids.append((m.group(1), m.group(2)))
print(f'Parsed IDs: {len(ids)}')
print('Sample IDs:', ids[:5])
