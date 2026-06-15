#!/usr/bin/env python3
"""
Brain knowledge search — SQLite FTS5, no external dependencies.

Usage:
  python brain/search.py "wireguard"         # найти тему
  python brain/search.py "n8n docker"        # несколько слов = OR-поиск
  python brain/search.py --build             # перестроить индекс
  python brain/search.py --build --verbose   # с деталями

Когда перестраивать индекс: после правок любого brain/*.md файла.
"""
import sys
import os
import sqlite3

# Безопасный вывод: utf-8 в Claude Code / Bash tool; замена символов в Windows cp1251 консоли
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BRAIN_DIR, '.knowledge.db')

# Файлы, которые не индексируем (навигационные / бинарные / сам скрипт)
SKIP = {
    'core.md',       # всегда в контексте, искать незачем
    'CHAT_INIT.md',  # инструкция для claude.ai, не для Code
    'Learn.md',      # личные заметки, не знания
    'search.py',
}


def chunk_file(path: str) -> list[tuple[str, str]]:
    """Разбить markdown на секции по заголовкам ## ."""
    with open(path, encoding='utf-8') as f:
        text = f.read()

    chunks = []
    title = '(header)'
    buf: list[str] = []

    for line in text.splitlines():
        if line.startswith('## '):
            if buf:
                body = '\n'.join(buf).strip()
                if body:
                    chunks.append((title, body))
            title = line[3:].strip()
            buf = []
        else:
            buf.append(line)

    if buf:
        body = '\n'.join(buf).strip()
        if body:
            chunks.append((title, body))

    return chunks


def build(verbose: bool = False) -> None:
    """Построить/перестроить FTS5 индекс из brain/*.md."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DROP TABLE IF EXISTS kb')
    conn.execute('''
        CREATE VIRTUAL TABLE kb USING fts5(
            file   UNINDEXED,
            section,
            body,
            tokenize="unicode61 remove_diacritics 1"
        )
    ''')

    total = 0
    for fname in sorted(os.listdir(BRAIN_DIR)):
        if fname in SKIP:
            continue
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(BRAIN_DIR, fname)
        chunks = chunk_file(fpath)
        for section, body in chunks:
            conn.execute('INSERT INTO kb VALUES (?,?,?)', (fname, section, body))
            total += 1
        if verbose:
            print(f'  {fname}: {len(chunks)} секций')

    conn.commit()
    conn.close()
    print(f'Индекс построен: {total} секций -> {DB_PATH}')


def search(query: str, limit: int = 5) -> None:
    """Найти релевантные секции по запросу."""
    if not os.path.exists(DB_PATH):
        print('Индекс не найден. Запусти: python brain/search.py --build')
        return

    # FTS5 OR-поиск: каждое слово в кавычках, объединяем через OR
    terms = [w for w in query.split() if w]
    if not terms:
        return
    fts_query = ' OR '.join(f'"{t}"' for t in terms)

    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            '''SELECT file, section, body, bm25(kb) AS rank
               FROM kb WHERE kb MATCH ?
               ORDER BY rank LIMIT ?''',
            (fts_query, limit),
        ).fetchall()
    except sqlite3.OperationalError as e:
        print(f'Ошибка поиска: {e}')
        conn.close()
        return

    conn.close()

    if not rows:
        print(f'Ничего не найдено по: {query!r}')
        print('Попробуй другие слова или читай brain/*.md напрямую.')
        return

    for file, section, body, _ in rows:
        print(f'\n{"-" * 60}')
        print(f'[{file}]  {section}')
        print('-' * 60)
        snippet = body.strip()[:800]
        if len(body.strip()) > 800:
            snippet += '\n...'
        print(snippet)


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    if args[0] == '--build':
        verbose = '--verbose' in args or '-v' in args
        build(verbose=verbose)
    else:
        search(' '.join(args))
