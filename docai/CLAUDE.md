# DocAI — контекст для Claude Code

> Загружается автоматически когда Claude Code работает в папке docai/

См. @context.md — цель, статус, что сделано, следующий шаг.

## Стек
- Python 3.11+, Windows
- PyQt6, pdfminer.six, fastembed, rank-bm25, anthropic, SQLite
- Запуск: `pip install -r requirements.txt && python app.py`

## Ключевые файлы
- `app.py` — PyQt6 GUI (главный)
- `docai.py` — PDF → JSON
- `ask.py` — RAG pipeline
- `db.py` — SQLite CRUD
- `build.py` — PyInstaller сборка в .exe

## Важно
- PyMuPDF даёт кракозябры для кириллицы — использовать pdfminer.six
- fastembed импортировать после установки FASTEMBED_CACHE_PATH в os.environ
