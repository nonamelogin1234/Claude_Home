#!/usr/bin/env python3
"""
DocAI — десктопное приложение для анализа проектной документации.
PyQt6 + SQLite + fastembed + Claude API.
"""

import sys
import os
import io
import json
import warnings
from pathlib import Path

warnings.filterwarnings('ignore', message='.*mean pooling.*')

# ─── Путь к данным модели ─────────────────────────────────────────────────────
# Устанавливаем до любых импортов fastembed
_app_data = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming')) / 'DocAI'
os.environ['FASTEMBED_CACHE_PATH'] = str(_app_data / 'models')

import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QFileDialog, QInputDialog, QProgressBar, QStatusBar,
    QMenu, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QSize, QTimer
)
from PyQt6.QtGui import QFont, QColor, QAction

import db

# ─── Цвета статусов ───────────────────────────────────────────────────────────
STATUS_COLORS = {
    'pending':    QColor('#888888'),
    'processing': QColor('#0066cc'),
    'ready':      QColor('#2a8c2a'),
    'error':      QColor('#cc2222'),
}
STATUS_LABELS = {
    'pending':    '[ ]',
    'processing': '[..]',
    'ready':      '[OK]',
    'error':      '[!]',
}


# ─── Фоновые воркеры ──────────────────────────────────────────────────────────

class ProcessWorker(QThread):
    """Обрабатывает PDF: docai extraction + build_index."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)   # (success, message)

    def __init__(self, file_id: int):
        super().__init__()
        self.file_id = file_id

    def run(self):
        try:
            file_rec = db.get_file(self.file_id)
            if not file_rec:
                self.finished.emit(False, "Файл не найден в базе")
                return

            pdf_path = file_rec['pdf_path']
            if not Path(pdf_path).exists():
                self.finished.emit(False, f"PDF не найден: {pdf_path}")
                return

            data_dir = db.file_data_dir(self.file_id)
            json_path = str(data_dir / 'extracted.json')

            db.update_file_status(self.file_id, 'processing')

            # ── Шаг 1: Извлечение текста ──
            self.progress.emit("Извлечение текста из PDF...")
            # Перенаправляем stdout чтобы поймать print() из docai
            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                import docai as docai_module
                result = docai_module.process_pdf(pdf_path, verbose=True)
            finally:
                sys.stdout = old_stdout

            for line in captured.getvalue().strip().splitlines():
                self.progress.emit(line)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.progress.emit(f"JSON сохранён: {Path(json_path).name}")

            # ── Шаг 2: Построение индекса ──
            self.progress.emit("Построение векторного индекса...")
            captured2 = io.StringIO()
            sys.stdout = captured2
            try:
                import ask as ask_module
                ask_module.build_index(json_path)
            finally:
                sys.stdout = old_stdout

            for line in captured2.getvalue().strip().splitlines():
                self.progress.emit(line)

            file_hash = db.pdf_hash(pdf_path)
            db.update_file_status(self.file_id, 'ready', file_hash=file_hash)
            self.finished.emit(True, "Готово")

        except Exception as e:
            db.update_file_status(self.file_id, 'error', error_msg=str(e))
            self.finished.emit(False, str(e))


class AskWorker(QThread):
    """Выполняет поиск и запрос к Claude в фоне."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)  # финальный ответ

    def __init__(self, question: str, json_paths: list[str], api_key: str):
        super().__init__()
        self.question = question
        self.json_paths = json_paths
        self.api_key = api_key

    def run(self):
        try:
            self.progress.emit("Поиск релевантных фрагментов...")
            chunks = _multi_search(self.json_paths, self.question, top_k=8)
            if not chunks:
                self.finished.emit("Индексированных файлов не найдено. Сначала обработайте PDF.")
                return

            self.progress.emit(f"Найдено {len(chunks)} фрагментов. Запрос к Claude...")
            os.environ['ANTHROPIC_API_KEY'] = self.api_key

            import ask as ask_module
            answer = ask_module.ask_claude(self.question, chunks)
            self.finished.emit(answer)

        except Exception as e:
            self.finished.emit(f"Ошибка: {e}")


# ─── Гибридный поиск по нескольким файлам ────────────────────────────────────

def _multi_search(json_paths: list[str], query: str, top_k: int = 8) -> list[dict]:
    """Поиск по нескольким индексам с объединением через RRF."""
    import ask as ask_module
    from fastembed import TextEmbedding
    from rank_bm25 import BM25Okapi

    if not json_paths:
        return []

    embedder = TextEmbedding(model_name=ask_module.EMBED_MODEL)
    query_vec = np.array(next(embedder.embed([query])), dtype=np.float32)

    all_chunks: list[dict] = []
    all_sem: list[float] = []
    all_bm25: list[float] = []

    for json_path in json_paths:
        vecs_path, meta_path = ask_module.index_paths(json_path)
        if not vecs_path.exists() or not meta_path.exists():
            continue
        vectors = np.load(str(vecs_path))
        with open(meta_path, encoding='utf-8') as f:
            meta = json.load(f)

        chunks = meta['chunks']
        source_name = Path(meta.get('source', json_path)).parent.name  # file_id dir

        sem_scores = ask_module.cosine_similarity(query_vec, vectors)
        tokenized = [ask_module.tokenize_ru(c['text']) for c in chunks]
        bm25 = BM25Okapi(tokenized)
        bm25_scores = bm25.get_scores(ask_module.tokenize_ru(query))

        for chunk, sem, bm25s in zip(chunks, sem_scores, bm25_scores):
            c = chunk.copy()
            c['_source'] = json_path
            all_chunks.append(c)
            all_sem.append(float(sem))
            all_bm25.append(float(bm25s))

    if not all_chunks:
        return []

    sem_ranked = sorted(range(len(all_sem)), key=lambda i: all_sem[i], reverse=True)
    bm25_ranked = sorted(range(len(all_bm25)), key=lambda i: all_bm25[i], reverse=True)
    rrf = ask_module.rrf_fuse([sem_ranked, bm25_ranked])

    top_indices = sorted(rrf, key=lambda i: rrf[i], reverse=True)[:top_k]
    results = []
    for idx in top_indices:
        c = all_chunks[idx].copy()
        c['score'] = all_sem[idx]
        c['bm25_score'] = all_bm25[idx]
        c['rrf_score'] = rrf[idx]
        results.append(c)
    return results


def _get_ready_json_paths(project_id: int = None) -> list[str]:
    """Возвращает пути к JSON готовых файлов (с индексом)."""
    files = db.get_files(project_id)
    paths = []
    for f in files:
        if f['status'] == 'ready':
            json_path = str(db.file_data_dir(f['id']) / 'extracted.json')
            if Path(json_path).exists():
                paths.append(json_path)
    return paths


# ─── Диалог настроек ─────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки DocAI")
        self.setMinimumWidth(480)

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("sk-ant-...")
        self.api_key_edit.setText(db.get_setting('anthropic_api_key'))
        layout.addRow("Anthropic API Key:", self.api_key_edit)

        info = QLabel(f"Данные приложения: {db.APP_DIR}")
        info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow(info)

        model_info = QLabel("Модель embeddings: paraphrase-multilingual-MiniLM-L12-v2\n"
                            f"Кэш модели: {db.MODELS_DIR}")
        model_info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addRow(model_info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save_and_accept(self):
        db.set_setting('anthropic_api_key', self.api_key_edit.text().strip())
        self.accept()


# ─── Главное окно ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocAI — Анализ проектной документации")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        self._active_workers: list[QThread] = []
        self._current_project_id: int | None = None

        self._setup_menu()
        self._setup_ui()
        self._refresh_tree()

    # ── Меню ─────────────────────────────────────────────────────────────────

    def _setup_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("Файл")

        act_settings = QAction("Настройки...", self)
        act_settings.triggered.connect(self._on_settings)
        file_menu.addAction(act_settings)

        file_menu.addSeparator()
        act_exit = QAction("Выход", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

    # ── Интерфейс ────────────────────────────────────────────────────────────

    def _setup_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # ── Левая панель ──
        left = QWidget()
        left.setMinimumWidth(280)
        left.setMaximumWidth(360)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(8, 8, 4, 8)

        hdr = QLabel("Проекты и файлы")
        hdr.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lv.addWidget(hdr)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        lv.addWidget(self.tree)

        # Кнопки под деревом
        btn_row = QWidget()
        bh = QHBoxLayout(btn_row)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(4)

        self.btn_new_project = QPushButton("+ Проект")
        self.btn_new_project.clicked.connect(self._on_add_project)
        bh.addWidget(self.btn_new_project)

        self.btn_add_file = QPushButton("+ PDF")
        self.btn_add_file.clicked.connect(self._on_add_file)
        bh.addWidget(self.btn_add_file)

        self.btn_process = QPushButton("▶ Обработать")
        self.btn_process.clicked.connect(self._on_process)
        bh.addWidget(self.btn_process)

        self.btn_delete = QPushButton("✕ Удалить")
        self.btn_delete.clicked.connect(self._on_delete)
        bh.addWidget(self.btn_delete)

        lv.addWidget(btn_row)
        splitter.addWidget(left)

        # ── Правая панель ──
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 8, 8, 8)
        rv.setSpacing(6)

        # Строка с областью поиска
        scope_row = QWidget()
        sh = QHBoxLayout(scope_row)
        sh.setContentsMargins(0, 0, 0, 0)
        sh.addWidget(QLabel("Поиск в:"))
        self.scope_combo = QComboBox()
        self.scope_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sh.addWidget(self.scope_combo)
        rv.addWidget(scope_row)

        # Область ответа
        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)
        self.answer_text.setFont(QFont("Consolas", 10))
        self.answer_text.setPlaceholderText(
            "Ответы на вопросы появятся здесь.\n\n"
            "Для начала:\n"
            "1. Создайте проект (+Проект)\n"
            "2. Добавьте PDF файл (+PDF)\n"
            "3. Обработайте файл (▶ Обработать)\n"
            "4. Задайте вопрос"
        )
        rv.addWidget(self.answer_text, stretch=1)

        # Лог обработки (свёрнут по умолчанию)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(120)
        self.log_text.setVisible(False)
        rv.addWidget(self.log_text)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setVisible(False)
        rv.addWidget(self.progress_bar)

        # Строка ввода
        input_row = QWidget()
        ih = QHBoxLayout(input_row)
        ih.setContentsMargins(0, 0, 0, 0)
        ih.setSpacing(6)

        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Задайте вопрос к документации...")
        self.question_input.setFont(QFont("Arial", 11))
        self.question_input.returnPressed.connect(self._on_ask)
        ih.addWidget(self.question_input)

        self.ask_btn = QPushButton("Спросить")
        self.ask_btn.setFixedWidth(100)
        self.ask_btn.setFont(QFont("Arial", 11))
        self.ask_btn.clicked.connect(self._on_ask)
        ih.addWidget(self.ask_btn)

        rv.addWidget(input_row)
        splitter.addWidget(right)

        splitter.setSizes([300, 700])

        # Статус-бар
        self.status_label = QLabel("Готов")
        self.statusBar().addWidget(self.status_label)

    # ── Дерево проектов ───────────────────────────────────────────────────────

    def _refresh_tree(self):
        self.tree.clear()
        projects = db.get_projects()
        for proj in projects:
            proj_item = QTreeWidgetItem([proj['name']])
            proj_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'project', 'id': proj['id']})
            proj_item.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))

            files = db.get_files(proj['id'])
            for f in files:
                status_label = STATUS_LABELS.get(f['status'], '[ ]')
                file_item = QTreeWidgetItem([f"{status_label} {f['display_name']}"])
                file_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'file', 'id': f['id']})
                color = STATUS_COLORS.get(f['status'], QColor('#888888'))
                file_item.setForeground(0, color)
                if f['error_msg']:
                    file_item.setToolTip(0, f"Ошибка: {f['error_msg']}")
                proj_item.addChild(file_item)

            self.tree.addTopLevelItem(proj_item)
            proj_item.setExpanded(True)

        self._refresh_scope_combo()

    def _refresh_scope_combo(self):
        self.scope_combo.clear()
        self.scope_combo.addItem("Все проекты", userData=None)
        for proj in db.get_projects():
            self.scope_combo.addItem(f"  {proj['name']}", userData=proj['id'])

    def _selected_item_data(self) -> dict | None:
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.ItemDataRole.UserRole)

    # ── Контекстное меню ─────────────────────────────────────────────────────

    def _on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        if data['type'] == 'project':
            menu.addAction("Переименовать", lambda: self._rename_project(data['id']))
            menu.addAction("+ Добавить PDF", lambda: self._add_file_to(data['id']))
            menu.addAction("▶ Обработать всё", lambda: self._process_project(data['id']))
            menu.addSeparator()
            menu.addAction("Удалить проект", lambda: self._delete_project(data['id']))

        elif data['type'] == 'file':
            menu.addAction("▶ Обработать", lambda: self._process_file(data['id']))
            menu.addSeparator()
            menu.addAction("Переместить в проект...", lambda: self._move_file(data['id']))
            menu.addAction("Удалить файл", lambda: self._delete_file(data['id']))

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    # ── Действия с проектами ─────────────────────────────────────────────────

    def _on_add_project(self):
        name, ok = QInputDialog.getText(self, "Новый проект", "Название проекта:")
        if ok and name.strip():
            try:
                db.create_project(name.strip())
                self._refresh_tree()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", str(e))

    def _rename_project(self, project_id: int):
        proj = next((p for p in db.get_projects() if p['id'] == project_id), None)
        if not proj:
            return
        name, ok = QInputDialog.getText(
            self, "Переименовать проект", "Новое название:", text=proj['name']
        )
        if ok and name.strip():
            db.rename_project(project_id, name.strip())
            self._refresh_tree()

    def _delete_project(self, project_id: int):
        proj = next((p for p in db.get_projects() if p['id'] == project_id), None)
        reply = QMessageBox.question(
            self, "Удалить проект",
            f"Удалить проект «{proj['name']}» и все его файлы из базы?\n"
            "(PDF файлы на диске не удаляются)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_project(project_id)
            self._refresh_tree()

    # ── Действия с файлами ───────────────────────────────────────────────────

    def _on_add_file(self):
        data = self._selected_item_data()
        if data and data['type'] == 'project':
            self._add_file_to(data['id'])
        elif data and data['type'] == 'file':
            # Добавить в тот же проект
            f = db.get_file(data['id'])
            if f:
                self._add_file_to(f['project_id'])
        else:
            QMessageBox.information(self, "Выберите проект",
                                    "Сначала выберите проект в дереве слева.")

    def _add_file_to(self, project_id: int):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Добавить PDF", "", "PDF файлы (*.pdf)"
        )
        for path in paths:
            name = Path(path).name
            db.add_file(project_id, name, path)
        if paths:
            self._refresh_tree()

    def _delete_file(self, file_id: int):
        f = db.get_file(file_id)
        reply = QMessageBox.question(
            self, "Удалить файл",
            f"Удалить «{f['display_name']}» из базы?\n(PDF на диске не удаляется)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.remove_file(file_id)
            self._refresh_tree()

    def _move_file(self, file_id: int):
        projects = db.get_projects()
        if not projects:
            return
        names = [p['name'] for p in projects]
        choice, ok = QInputDialog.getItem(
            self, "Переместить файл", "Выберите проект:", names, editable=False
        )
        if ok and choice:
            target = next(p for p in projects if p['name'] == choice)
            db.move_file(file_id, target['id'])
            self._refresh_tree()

    # ── Обработка ────────────────────────────────────────────────────────────

    def _on_process(self):
        data = self._selected_item_data()
        if not data:
            QMessageBox.information(self, "Выбор", "Выберите проект или файл.")
            return
        if data['type'] == 'project':
            self._process_project(data['id'])
        else:
            self._process_file(data['id'])

    def _process_project(self, project_id: int):
        files = db.get_files(project_id)
        for f in files:
            if db.file_needs_reindex(f['id']):
                self._process_file(f['id'])

    def _process_file(self, file_id: int):
        if not db.file_needs_reindex(file_id):
            self.status_label.setText("Файл уже актуален.")
            return

        self.log_text.clear()
        self.log_text.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Режим анимации

        worker = ProcessWorker(file_id)
        worker.progress.connect(self._on_process_progress)
        worker.finished.connect(lambda ok, msg: self._on_process_done(file_id, ok, msg))
        self._active_workers.append(worker)
        worker.start()

        self.status_label.setText("Обработка файла...")
        self._refresh_tree()

    def _on_process_progress(self, msg: str):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _on_process_done(self, file_id: int, success: bool, message: str):
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        if success:
            self.status_label.setText(f"Файл обработан успешно.")
        else:
            self.status_label.setText(f"Ошибка: {message}")
            QMessageBox.warning(self, "Ошибка обработки", message)
        self._refresh_tree()
        # Скрываем лог через 5 сек
        QTimer.singleShot(5000, lambda: self.log_text.setVisible(False))

    # ── Поиск и вопросы ───────────────────────────────────────────────────────

    def _on_selection_changed(self):
        """Синхронизирует scope_combo с выбором в дереве."""
        data = self._selected_item_data()
        if not data:
            self.scope_combo.setCurrentIndex(0)
            return
        if data['type'] == 'project':
            for i in range(self.scope_combo.count()):
                if self.scope_combo.itemData(i) == data['id']:
                    self.scope_combo.setCurrentIndex(i)
                    return
        elif data['type'] == 'file':
            f = db.get_file(data['id'])
            if f:
                for i in range(self.scope_combo.count()):
                    if self.scope_combo.itemData(i) == f['project_id']:
                        self.scope_combo.setCurrentIndex(i)
                        return

    def _on_delete(self):
        data = self._selected_item_data()
        if not data:
            QMessageBox.information(self, "Выбор", "Выберите проект или файл.")
            return
        if data['type'] == 'project':
            self._delete_project(data['id'])
        else:
            self._delete_file(data['id'])

    def _on_ask(self):
        question = self.question_input.text().strip()
        if not question:
            return

        api_key = db.get_setting('anthropic_api_key')
        if not api_key:
            QMessageBox.warning(
                self, "API Key не задан",
                "Укажите Anthropic API Key в Файл → Настройки."
            )
            return

        # Определяем область поиска
        scope_project_id = self.scope_combo.currentData()
        json_paths = _get_ready_json_paths(scope_project_id)

        if not json_paths:
            scope_name = self.scope_combo.currentText().strip()
            QMessageBox.information(
                self, "Нет индексированных файлов",
                f"В «{scope_name}» нет обработанных файлов.\n"
                "Добавьте PDF и нажмите ▶ Обработать."
            )
            return

        self.ask_btn.setEnabled(False)
        self.question_input.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.answer_text.setPlainText("")

        worker = AskWorker(question, json_paths, api_key)
        worker.progress.connect(lambda msg: self.status_label.setText(msg))
        worker.finished.connect(self._on_ask_done)
        self._active_workers.append(worker)
        worker.start()

    def _on_ask_done(self, answer: str):
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.ask_btn.setEnabled(True)
        self.question_input.setEnabled(True)
        self.status_label.setText("Готов")

        # Добавляем вопрос и ответ в историю
        q = self.question_input.text().strip()
        current = self.answer_text.toPlainText()
        separator = "\n" + "─" * 60 + "\n" if current else ""
        self.answer_text.setPlainText(
            current + separator +
            f"Вопрос: {q}\n\n{answer}\n"
        )
        self.answer_text.verticalScrollBar().setValue(
            self.answer_text.verticalScrollBar().maximum()
        )

    # ── Настройки ────────────────────────────────────────────────────────────

    def _on_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def closeEvent(self, event):
        # Ждём завершения воркеров
        for w in self._active_workers:
            w.quit()
            w.wait(2000)
        super().closeEvent(event)


# ─── Точка входа ──────────────────────────────────────────────────────────────

def main():
    db.init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("DocAI")
    app.setStyle("Fusion")

    # Шрифт с поддержкой кириллицы
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
