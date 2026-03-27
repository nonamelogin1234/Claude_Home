#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Fix Windows console encoding
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
DocAI RAG — вопросы к PDF-документации через локальные embeddings + Claude.

Использование:
    # Построить индекс (один раз):
    python ask.py --build test_output.json

    # Задать вопрос:
    python ask.py "какая высота этажа?"
    python ask.py "где упоминается отметка -1.200?"
    python ask.py --json test_output.json "площадь застройки"
"""

import sys
import os
import json
import re
import argparse
import textwrap
import warnings
from pathlib import Path

# Fastembed предупреждает о смене pooling в новых версиях — это норма
warnings.filterwarnings('ignore', message='.*mean pooling.*')

import numpy as np

# ─── Константы ────────────────────────────────────────────────────────────────

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 6          # Сколько чанков передавать в Claude
CHUNK_MAX = 600    # Максимальная длина чанка в символах
CHUNK_MIN = 80     # Минимальная длина — меньше мержится с соседом


# ─── Чанкинг ─────────────────────────────────────────────────────────────────

def chunk_json(json_path: str) -> list[dict]:
    """Читает JSON от docai.py и возвращает список чанков с метаданными."""
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    chunks = []
    source_file = data.get('source_file', Path(json_path).name)

    for page in data['pages']:
        page_num = page['page_number']
        method = page['extraction_method']

        # Пропускаем страницы с мусором или неудавшимся OCR
        if method == 'failed_no_ocr':
            continue

        raw_blocks = page.get('text_blocks', [])
        texts = [b['text'].strip() for b in raw_blocks if b['text'].strip()]

        # Мержим очень короткие блоки с предыдущим
        merged: list[str] = []
        for t in texts:
            if merged and len(t) < CHUNK_MIN and len(merged[-1]) + len(t) < CHUNK_MAX:
                merged[-1] += '\n' + t
            else:
                merged.append(t)

        # Разбиваем длинные блоки по предложениям/абзацам
        final_texts: list[str] = []
        for t in merged:
            if len(t) <= CHUNK_MAX:
                final_texts.append(t)
            else:
                # Сплитим по предложениям (. или \n)
                sentences = re.split(r'(?<=[.!?])\s+|\n{2,}', t)
                buf = ''
                for sent in sentences:
                    if len(buf) + len(sent) + 1 <= CHUNK_MAX:
                        buf = (buf + ' ' + sent).strip() if buf else sent
                    else:
                        if buf:
                            final_texts.append(buf)
                        buf = sent[:CHUNK_MAX]
                if buf:
                    final_texts.append(buf)

        for i, text in enumerate(final_texts):
            # Префикс с номером страницы — помогает Claude ориентироваться
            chunk_text = f"[Стр. {page_num}] {text}"
            chunks.append({
                "id": len(chunks),
                "page": page_num,
                "text": chunk_text,
                "raw_text": text,
                "char_count": len(text),
            })

    # Добавляем специальные чанки из all_numbers (отметки, площади, размеры)
    # — они важны для точного поиска числовых значений
    important_types = {'отметка', 'площадь', 'размер', 'объём', 'нагрузка', 'размер_м'}
    seen_contexts: set[str] = set()
    for num in data.get('all_numbers', []):
        if num.get('type') not in important_types:
            continue
        ctx = num.get('context', '').strip()
        if not ctx or ctx in seen_contexts:
            continue
        seen_contexts.add(ctx)
        pg = num.get('page', '?')
        val = num.get('value', '')
        num_type = num.get('type', '')
        chunk_text = f"[Стр. {pg}] [{num_type}: {val}] {ctx}"
        chunks.append({
            "id": len(chunks),
            "page": pg,
            "text": chunk_text,
            "raw_text": ctx,
            "char_count": len(ctx),
            "number_type": num_type,
            "number_value": val,
        })

    print(f"  Чанков создано: {len(chunks)}")
    return chunks


# ─── Embeddings ───────────────────────────────────────────────────────────────

def get_embedder():
    """Загружает модель embeddings (скачивает при первом запуске ~220MB)."""
    from fastembed import TextEmbedding
    print(f"  Загрузка модели: {EMBED_MODEL}")
    return TextEmbedding(model_name=EMBED_MODEL)


def embed_texts(embedder, texts: list[str]) -> np.ndarray:
    """Возвращает numpy array (N, dim) с эмбеддингами."""
    vectors = list(embedder.embed(texts, batch_size=32))
    return np.array(vectors, dtype=np.float32)


# ─── Индекс ───────────────────────────────────────────────────────────────────

def index_paths(json_path: str) -> tuple[Path, Path]:
    """Возвращает пути к файлам индекса рядом с JSON."""
    base = Path(json_path).with_suffix('')
    return base.with_suffix('.vecs.npy'), base.with_suffix('.meta.json')


def build_index(json_path: str):
    """Создаёт индекс векторов из JSON файла docai."""
    print(f"Строю индекс: {json_path}")

    chunks = chunk_json(json_path)
    texts = [c['text'] for c in chunks]

    embedder = get_embedder()
    print(f"  Вычисляю эмбеддинги для {len(texts)} чанков...")
    vectors = embed_texts(embedder, texts)

    vecs_path, meta_path = index_paths(json_path)

    np.save(str(vecs_path), vectors)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({
            "model": EMBED_MODEL,
            "source": json_path,
            "chunks": chunks,
        }, f, ensure_ascii=False, indent=2)

    print(f"  Сохранено: {vecs_path.name} ({vectors.shape})")
    print(f"  Сохранено: {meta_path.name}")
    print("Индекс готов.")


# ─── Поиск ───────────────────────────────────────────────────────────────────

def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Косинусное сходство query (dim,) против matrix (N, dim)."""
    q = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
    normed = matrix / norms
    return normed @ q


def tokenize_ru(text: str) -> list[str]:
    """Простая токенизация для BM25 (нижний регистр, слова)."""
    return re.findall(r'[а-яёa-z0-9,.\-+]+', text.lower())


def rrf_fuse(ranked_lists: list[list[int]], k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion: объединяет несколько ranked lists."""
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, idx in enumerate(ranked):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return scores


def search(json_path: str, query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Гибридный поиск: семантика (embeddings) + ключевые слова (BM25),
    объединённые через Reciprocal Rank Fusion.
    """
    vecs_path, meta_path = index_paths(json_path)

    if not vecs_path.exists() or not meta_path.exists():
        print(f"Индекс не найден. Запустите: python ask.py --build {json_path}")
        sys.exit(1)

    vectors = np.load(str(vecs_path))
    with open(meta_path, encoding='utf-8') as f:
        meta = json.load(f)

    chunks = meta['chunks']
    model_name = meta.get('model', EMBED_MODEL)
    n = len(chunks)

    # ── Семантический поиск ──
    from fastembed import TextEmbedding
    embedder = TextEmbedding(model_name=model_name)
    query_vec = next(embedder.embed([query]))
    sem_scores = cosine_similarity(np.array(query_vec, dtype=np.float32), vectors)
    sem_ranked = list(np.argsort(sem_scores)[::-1])

    # ── BM25 поиск ──
    from rank_bm25 import BM25Okapi
    tokenized_corpus = [tokenize_ru(c['text']) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(tokenize_ru(query))
    bm25_ranked = list(np.argsort(bm25_scores)[::-1])

    # ── RRF слияние ──
    rrf_scores = rrf_fuse([sem_ranked, bm25_ranked])
    top_indices = sorted(rrf_scores, key=lambda i: rrf_scores[i], reverse=True)[:top_k]

    results = []
    for idx in top_indices:
        chunk = chunks[int(idx)].copy()
        chunk['score'] = float(sem_scores[int(idx)])   # показываем семантический скор
        chunk['bm25_score'] = float(bm25_scores[int(idx)])
        chunk['rrf_score'] = rrf_scores[int(idx)]
        results.append(chunk)

    # Сортируем по rrf_score для отображения
    results.sort(key=lambda x: x['rrf_score'], reverse=True)
    return results


# ─── Ответ через Claude ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """Ты — помощник по анализу российской строительной проектной документации.
Тебе предоставлены извлечённые фрагменты из документации (PDF → JSON → RAG поиск).
Отвечай точно, ссылаясь на страницы документа где это уместно.
Если информации недостаточно — так и скажи. Не придумывай данные."""


def ask_claude(question: str, context_chunks: list[dict]) -> str:
    """Отправляет вопрос + контекст в Claude и возвращает ответ."""
    import anthropic

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return (
            "Ошибка: переменная ANTHROPIC_API_KEY не установлена.\n"
            "Установите её: set ANTHROPIC_API_KEY=sk-ant-..."
        )

    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        score_str = f"(релевантность: {chunk['score']:.2f})"
        context_parts.append(f"--- Фрагмент {i} {score_str} ---\n{chunk['text']}")

    context_str = "\n\n".join(context_parts)

    user_message = (
        f"Фрагменты документации:\n\n{context_str}\n\n"
        f"Вопрос: {question}"
    )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


# ─── CLI ─────────────────────────────────────────────────────────────────────

def find_index(start_dir: str = '.') -> str | None:
    """Ищет .meta.json файл индекса в текущей директории."""
    for path in Path(start_dir).glob('*.meta.json'):
        return str(path.with_suffix('').with_suffix('').with_suffix('.json'))
    return None


def main():
    parser = argparse.ArgumentParser(
        description='DocAI RAG — вопросы к проектной документации'
    )
    parser.add_argument('question', nargs='?', help='Вопрос к документации')
    parser.add_argument('--build', metavar='JSON', help='Построить индекс из JSON файла docai')
    parser.add_argument('--json', metavar='JSON', help='Явно указать JSON файл для поиска')
    parser.add_argument('-k', type=int, default=TOP_K, help=f'Количество чанков (по умолчанию {TOP_K})')
    parser.add_argument('--no-llm', action='store_true', help='Только показать найденные чанки, без Claude')
    args = parser.parse_args()

    if args.build:
        build_index(args.build)
        return

    if not args.question:
        parser.print_help()
        return

    # Определяем JSON файл
    json_path = args.json
    if not json_path:
        # Ищем автоматически
        json_path = find_index('.')
        if not json_path:
            print("JSON файл не найден. Укажите: python ask.py --json <file.json> \"вопрос\"")
            sys.exit(1)

    print(f"Ищу в: {json_path}")
    chunks = search(json_path, args.question, top_k=args.k)

    print(f"\nНайдено {len(chunks)} релевантных фрагментов:")
    for c in chunks:
        sem = c['score']
        bm25 = c.get('bm25_score', 0)
        rrf = c.get('rrf_score', sem)
        score_bar = '|' * int(rrf * 600)
        preview = c['text'][:120].replace('\n', ' ')
        print(f"  sem={sem:.3f} bm25={bm25:.1f} rrf={rrf:.4f} {score_bar}")
        print(f"    {preview}")
        print()

    if args.no_llm:
        return

    print("─" * 60)
    print(f"Вопрос: {args.question}")
    print("─" * 60)
    answer = ask_claude(args.question, chunks)
    print(answer)


if __name__ == '__main__':
    main()
