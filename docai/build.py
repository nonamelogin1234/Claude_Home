"""
Сборка DocAI в .exe через PyInstaller.

Запуск:
    python build.py

Результат: dist/DocAI.exe (один файл)

Что входит в exe: Python, PyQt6, fastembed, onnxruntime, pdfminer, PyMuPDF,
                   pytesseract, rank_bm25, anthropic, db.py, app.py, docai.py, ask.py

Что НЕ входит: модель embeddings (скачивается в %APPDATA%/DocAI/models/ при первом запуске)
"""

import subprocess
import sys
import shutil
from pathlib import Path

# Файлы приложения
DATA_FILES = ['docai.py', 'ask.py', 'db.py']
ICON = None   # 'icon.ico' если есть

def build():
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',           # без консоли (GUI приложение)
        '--name', 'DocAI',
        '--clean',
        # Включаем все нужные модули явно
        '--hidden-import', 'fastembed',
        '--hidden-import', 'onnxruntime',
        '--hidden-import', 'rank_bm25',
        '--hidden-import', 'anthropic',
        '--hidden-import', 'pdfminer',
        '--hidden-import', 'pdfminer.high_level',
        '--hidden-import', 'pdfminer.layout',
        '--hidden-import', 'fitz',
        '--hidden-import', 'pytesseract',
        '--hidden-import', 'PIL',
        '--hidden-import', 'numpy',
        '--hidden-import', 'PyQt6',
        '--hidden-import', 'PyQt6.QtWidgets',
        '--hidden-import', 'PyQt6.QtCore',
        '--hidden-import', 'PyQt6.QtGui',
        '--hidden-import', 'tokenizers',
        '--hidden-import', 'huggingface_hub',
    ]

    # Добавляем data файлы (docai.py, ask.py, db.py рядом с exe)
    for f in DATA_FILES:
        if Path(f).exists():
            cmd += ['--add-data', f'{f};.']

    if ICON and Path(ICON).exists():
        cmd += ['--icon', ICON]

    cmd.append('app.py')

    print("Запуск PyInstaller...")
    print(' '.join(cmd))
    print()

    result = subprocess.run(cmd)
    if result.returncode == 0:
        exe = Path('dist/DocAI.exe')
        size_mb = exe.stat().st_size / 1024 / 1024 if exe.exists() else 0
        print(f"\n=== Готово! ===")
        print(f"Файл: {exe.resolve()}")
        print(f"Размер: {size_mb:.1f} MB")
        print()
        print("Примечание: при первом запуске DocAI.exe скачает модель embeddings")
        print(f"(~220MB) в %APPDATA%\\DocAI\\models\\")
    else:
        print("\n=== Сборка завершилась с ошибкой ===")
        sys.exit(1)


if __name__ == '__main__':
    build()
