with open('C:/Users/user/Documents/Claude_Home/kinoclaude/kinoclaude_ratings.md', 'r', encoding='utf-16') as f:
    lines = f.readlines()

# Print ALL columns for first 10 lines
print('=== Full columns ===')
for l in lines[:10]:
    cols = l.strip().split('\t')
    for i, c in enumerate(cols):
        print(f'  col{i}: {repr(c[:60])}')
    print()
