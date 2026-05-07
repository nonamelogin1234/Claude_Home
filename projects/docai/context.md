# 🔍 DocAI

## ЦЕЛЬ
Локальный инструмент для анализа PDF проектной документации (строительство, кириллица).
PDF → JSON → RAG поиск → ответы через Claude API.

## СТАТУС
🟡 В процессе — LLM переключён на OpenAI (gpt-4o), требует тестирования на реальном PDF

## ЧТО СДЕЛАНО
- [2026-03-xx] v1: docai.py — PDF → JSON через pdfminer.six (решает Identity encoding для кириллицы)
- [2026-03-xx] v2: ask.py — RAG pipeline (fastembed + BM25 + RRF + Claude API)
- [2026-03-xx] v3: app.py — PyQt6 GUI с проектами, SQLite БД, фоновая обработка
- [2026-03-xx] build.py — PyInstaller сборка в .exe
- [2026-03-27] Код перенесён в репо Claude_Home/docai/
- [2026-03-27] LLM переключён с Anthropic Claude на OpenAI gpt-4o (ask.py + app.py + requirements.txt)

## СЛЕДУЮЩИЙ ШАГ
Протестировать app.py на реальном PDF: вставить OpenAI API ключ в Файл → Настройки, загрузить PDF.

## ГРАБЛИ
- PyMuPDF даёт кракозябры для кириллицы (Identity encoding) — использовать pdfminer.six
- Чертёжные страницы pdfminer разбивает на отдельные символы — OCR помогает
- fastembed импортировать после установки FASTEMBED_CACHE_PATH в os.environ

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
```
Стек: PyQt6, pdfminer.six, fastembed, rank-bm25, openai, SQLite
БД: %APPDATA%\DocAI\docai.db
Данные: %APPDATA%\DocAI\data\{file_id}\
Модель embeddings: paraphrase-multilingual-MiniLM-L12-v2 (~220MB)
LLM: gpt-4o (OpenAI)
Ключ: хранится в БД как openai_api_key, передаётся через env OPENAI_API_KEY
Запуск: pip install -r requirements.txt && python app.py
```
