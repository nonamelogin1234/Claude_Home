# 🔍 DocAI

## ЦЕЛЬ
Локальный инструмент для анализа PDF проектной документации (строительство, кириллица).
PDF → JSON → RAG поиск → ответы через Claude API.

## СТАТУС
🟡 В процессе — v3 (app.py) готов, требует тестирования на реальном PDF

## ЧТО СДЕЛАНО
- [2026-03-xx] v1: docai.py — PDF → JSON через pdfminer.six (решает Identity encoding для кириллицы)
- [2026-03-xx] v2: ask.py — RAG pipeline (fastembed + BM25 + RRF + Claude API)
- [2026-03-xx] v3: app.py — PyQt6 GUI с проектами, SQLite БД, фоновая обработка
- [2026-03-xx] build.py — PyInstaller сборка в .exe
- [2026-03-27] Код перенесён в репо Claude_Home/docai/

## СЛЕДУЮЩИЙ ШАГ
Протестировать app.py на реальном PDF из проекта Тентюки или Агалатово.

## ГРАБЛИ
- PyMuPDF даёт кракозябры для кириллицы (Identity encoding) — использовать pdfminer.six
- Чертёжные страницы pdfminer разбивает на отдельные символы — OCR помогает
- fastembed импортировать после установки FASTEMBED_CACHE_PATH в os.environ

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
```
Стек: PyQt6, pdfminer.six, fastembed, rank-bm25, anthropic, SQLite
БД: %APPDATA%\DocAI\docai.db
Данные: %APPDATA%\DocAI\data\{file_id}\
Модель: paraphrase-multilingual-MiniLM-L12-v2 (~220MB)
LLM: claude-sonnet-4-6
Запуск: pip install -r requirements.txt && python app.py
```
