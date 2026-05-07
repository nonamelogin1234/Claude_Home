# DocAI — Анализ проектной документации

Локальный инструмент для работы с PDF проектной документации (строительство, архитектура).

## Версии
- **v1** `docai.py` — PDF → JSON (извлечение текста и чисел)
- **v2** `ask.py` — RAG: локальный поиск по чанкам + ответы через Claude API  
- **v3** `app.py` — PyQt6 десктопное приложение с проектами, БД и GUI

## Стек
- pdfminer.six — извлечение текста (решает Identity encoding для кириллицы)
- fastembed — локальные embeddings без PyTorch
- rank-bm25 — BM25 поиск
- RRF — гибридный поиск (semantic + BM25)
- SQLite — постоянная база данных
- PyQt6 — GUI

## Запуск
```
pip install PyQt6 fastembed rank-bm25 anthropic pdfminer.six numpy
python app.py
```
