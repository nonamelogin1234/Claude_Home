#!/usr/bin/env python3
"""
DocAI — PDF → JSON для анализа проектной документации.

Использование:
    python docai.py input.pdf [output.json]

Если output.json не указан — создаётся рядом с PDF с тем же именем.
"""

import sys
import os
import re
import json
import datetime
import argparse
from pathlib import Path
from typing import Optional


# ─── Утилиты ─────────────────────────────────────────────────────────────────

def is_cyrillic_text(text: str, threshold: float = 0.05) -> bool:
    """
    Проверяет, содержит ли текст достаточно кириллических символов.
    threshold — доля кириллицы от всех буквенных символов.
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    cyrillic = [c for c in letters if '\u0400' <= c <= '\u04FF']
    return len(cyrillic) / len(letters) >= threshold


def is_garbled(text: str) -> bool:
    """
    Детектирует мусорный текст.
    Признаки: много символов замены (U+FFFD) или символов из диапазона
    частных использований, или почти нет читаемых букв при наличии контента.
    """
    if not text.strip():
        return False
    replacement = text.count('\ufffd')
    if replacement > 3:
        return True
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    # В проектной документации на русском должна быть кириллица
    # Если букв много, но кириллицы нет — скорее всего мусор
    cyrillic = [c for c in letters if '\u0400' <= c <= '\u04FF']
    latin = [c for c in letters if 'a' <= c.lower() <= 'z']
    # Если нет ни кириллицы ни латиницы — мусор
    if len(cyrillic) + len(latin) == 0 and len(letters) > 5:
        return True
    return False


# ─── Извлечение чисел с контекстом ───────────────────────────────────────────

# Паттерны для типичных чисел в проектной документации
NUMBER_PATTERNS = [
    # Отметки со знаком: ±0.000, -1.200, +3.500, -0,030
    (r'[±+\-]\d+[.,]\d{3}', 'отметка'),
    # Отметка 0.000 / 0,000 (нулевая отметка без знака, именно три знака)
    (r'\b0[.,]000\b', 'отметка'),
    # Размеры в мм с разделителем х/×/x: 3000×2100, 12,73 х 10,74
    (r'\d+[.,]?\d*\s*[хx×]\s*\d+[.,]?\d*(?:\s*[хx×]\s*\d+[.,]?\d*)?', 'размер'),
    # Площади: 45.2 м², 161,9 м2, 125,4 кв.м, 32,6 м²
    (r'\d+[.,]\d+\s*(?:м[2²]|кв\.?\s*м|m[2²])', 'площадь'),
    # Площади без дроби с единицами: 100 м2
    (r'\d+\s*(?:м[2²]|кв\.?\s*м)\b', 'площадь'),
    # Объёмы: 250 м³, 616,8 м3
    (r'\d+[.,]?\d*\s*м[3³]', 'объём'),
    # Нагрузки и давления: 150 кг/м², 2.5 кН/м
    (r'\d+[.,]?\d*\s*(?:кг/м[2²]?|кН/м[2²]?|т/м[2²]?|МПа|кПа)', 'нагрузка'),
    # Высоты/длины с единицами м: 3.17 м, 5,17 м (одиночное число + м)
    (r'\d+[.,]\d+\s*м\b', 'размер_м'),
    # Количества: числа рядом со шт, м.п., п.м.
    (r'\d+[.,]?\d*\s*(?:шт\.?|п\.?\s*м\.?|м\.?\s*п\.?|рул\.?|уп\.?)', 'количество'),
    # Числа с десятичной точкой/запятой (общий fallback)
    (r'\d+[.,]\d+', 'число'),
    # Целые числа от 4 цифр (крупные размеры)
    (r'\b\d{4,}\b', 'число'),
]


def extract_numbers(text: str) -> list[dict]:
    """Извлекает числа с типом и контекстом из текста."""
    results = []
    seen_spans = set()

    for pattern, num_type in NUMBER_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            span = (m.start(), m.end())
            # Не дублировать уже найденные позиции
            if any(s[0] <= span[0] <= s[1] or s[0] <= span[1] <= s[1] for s in seen_spans):
                continue
            seen_spans.add(span)

            # Контекст: 60 символов до и после
            ctx_start = max(0, m.start() - 60)
            ctx_end = min(len(text), m.end() + 60)
            context = text[ctx_start:ctx_end].replace('\n', ' ').strip()

            results.append({
                "value": m.group().strip(),
                "type": num_type,
                "context": context,
                "position": m.start(),
            })

    results.sort(key=lambda x: x['position'])
    # Убираем поле position из финального вывода
    for r in results:
        del r['position']
    return results


# ─── Извлечение через pdfminer ────────────────────────────────────────────────

def extract_with_pdfminer(pdf_path: str) -> list[dict]:
    """
    Основной метод извлечения через pdfminer.six.
    Возвращает список страниц с текстом и метаданными.
    """
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import (LTPage, LTTextBox, LTTextLine, LTChar,
                                  LTAnno, LTRect, LTFigure, LTImage,
                                  LTLayoutContainer)

    pages_data = []

    for page_num, page_layout in enumerate(extract_pages(pdf_path), start=1):
        page_width = page_layout.width
        page_height = page_layout.height

        text_blocks = []
        has_figures = False

        for element in page_layout:
            if isinstance(element, LTTextBox):
                raw_text = element.get_text()
                if not raw_text.strip():
                    continue

                lines = []
                for line in element:
                    if isinstance(line, LTTextLine):
                        line_text = line.get_text().rstrip('\n')
                        if line_text.strip():
                            lines.append(line_text)

                block_text = '\n'.join(lines)
                bbox = [round(v, 1) for v in element.bbox]

                text_blocks.append({
                    "block_id": len(text_blocks) + 1,
                    "bbox": bbox,  # [x0, y0, x1, y1] от нижнего левого угла
                    "text": block_text,
                    "numbers": extract_numbers(block_text),
                })

            elif isinstance(element, LTFigure):
                has_figures = True

        full_text = '\n\n'.join(b['text'] for b in text_blocks)
        garbled = is_garbled(full_text)

        pages_data.append({
            "page_number": page_num,
            "page_size": {"width": round(page_width, 1), "height": round(page_height, 1)},
            "extraction_method": "pdfminer",
            "has_figures": has_figures,
            "is_garbled": garbled,
            "text_blocks": text_blocks,
            "full_text": full_text,
            "numbers": extract_numbers(full_text),
        })

    return pages_data


# ─── OCR через Tesseract (опционально) ───────────────────────────────────────

def find_tesseract() -> Optional[str]:
    """Ищет tesseract.exe в стандартных местах на Windows."""
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\gor-r\AppData\Local\Tesseract-OCR\tesseract.exe",
    ]
    # Проверить PATH
    import shutil
    found = shutil.which("tesseract")
    if found:
        return found
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def ocr_page(page_num: int, pdf_path: str, tesseract_path: str) -> Optional[dict]:
    """OCR одной страницы через Tesseract."""
    try:
        import pytesseract
        import fitz  # PyMuPDF для рендеринга
        from PIL import Image
        import io

        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        # 300 DPI: mat = fitz.Matrix(300/72, 300/72)
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        ocr_text = pytesseract.image_to_string(img, lang='rus+eng', config='--oem 3 --psm 6')

        return {
            "page_number": page_num,
            "page_size": {
                "width": round(page.rect.width, 1),
                "height": round(page.rect.height, 1),
            },
            "extraction_method": "tesseract_ocr",
            "has_figures": True,
            "is_garbled": False,
            "text_blocks": [{
                "block_id": 1,
                "bbox": None,
                "text": ocr_text,
                "numbers": extract_numbers(ocr_text),
            }],
            "full_text": ocr_text,
            "numbers": extract_numbers(ocr_text),
        }
    except Exception as e:
        print(f"  [OCR ошибка стр.{page_num}]: {e}", file=sys.stderr)
        return None


# ─── Основная логика ──────────────────────────────────────────────────────────

def process_pdf(pdf_path: str, verbose: bool = True) -> dict:
    """Полная обработка PDF → структурированный словарь."""
    if verbose:
        print(f"Обработка: {pdf_path}")

    pdf_path = str(Path(pdf_path).resolve())
    tesseract_path = find_tesseract()
    if verbose:
        if tesseract_path:
            print(f"  Tesseract найден: {tesseract_path}")
        else:
            print("  Tesseract не найден — OCR недоступен")

    # Извлекаем через pdfminer
    if verbose:
        print("  Извлечение текста (pdfminer)...")
    pages = extract_with_pdfminer(pdf_path)

    if verbose:
        print(f"  Страниц: {len(pages)}")

    # Для страниц с мусорным текстом или без текста — пробуем OCR
    for i, page in enumerate(pages):
        needs_ocr = page['is_garbled'] or (
            not page['full_text'].strip() and page['has_figures']
        )
        if needs_ocr:
            if tesseract_path:
                if verbose:
                    print(f"  Стр.{page['page_number']}: мусор/пусто → OCR")
                ocr_result = ocr_page(page['page_number'], pdf_path, tesseract_path)
                if ocr_result:
                    pages[i] = ocr_result
            else:
                if verbose:
                    print(f"  Стр.{page['page_number']}: мусор/пусто, OCR недоступен — пропускаем")
                pages[i]['extraction_method'] = 'failed_no_ocr'

    # Собираем сводку по числам по всему документу
    all_numbers = []
    for page in pages:
        for num in page['numbers']:
            all_numbers.append({
                "page": page['page_number'],
                **num,
            })

    # Группировка по значению — удобно для поиска противоречий
    from collections import defaultdict
    value_index: dict[str, list] = defaultdict(list)
    for item in all_numbers:
        key = item['value'].strip()
        value_index[key].append({
            "page": item['page'],
            "type": item['type'],
            "context": item['context'],
        })
    # Только значения, встречающиеся на 2+ страницах (потенциальные противоречия)
    cross_page = {
        val: occurrences
        for val, occurrences in value_index.items()
        if len({o['page'] for o in occurrences}) >= 2
    }

    result = {
        "docai_version": "1.0",
        "source_file": os.path.basename(pdf_path),
        "source_path": pdf_path,
        "extracted_at": datetime.datetime.now().isoformat(),
        "total_pages": len(pages),
        "pages": pages,
        "all_numbers": all_numbers,
        "cross_page_values": cross_page,
        "stats": {
            "pages_with_text": sum(1 for p in pages if p['full_text'].strip()),
            "pages_garbled": sum(1 for p in pages if p['is_garbled']),
            "pages_ocr": sum(1 for p in pages if p['extraction_method'] == 'tesseract_ocr'),
            "total_numbers_found": len(all_numbers),
            "unique_values": len(value_index),
            "cross_page_values": len(cross_page),
        }
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description='DocAI — извлечение текста и чисел из PDF проектной документации в JSON'
    )
    parser.add_argument('pdf', help='Путь к PDF файлу')
    parser.add_argument('output', nargs='?', help='Путь к выходному JSON (по умолчанию — рядом с PDF)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Не выводить прогресс')
    args = parser.parse_args()

    pdf_path = args.pdf
    if not os.path.isfile(pdf_path):
        print(f"Ошибка: файл не найден: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        output_path = str(Path(pdf_path).with_suffix('.json'))

    result = process_pdf(pdf_path, verbose=not args.quiet)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if not args.quiet:
        stats = result['stats']
        print(f"\nГотово: {output_path}")
        print(f"  Страниц с текстом:    {stats['pages_with_text']}/{result['total_pages']}")
        print(f"  Страниц с мусором:    {stats['pages_garbled']}")
        print(f"  Страниц через OCR:    {stats['pages_ocr']}")
        print(f"  Числа/значения найдено: {stats['total_numbers_found']}")


if __name__ == '__main__':
    main()
