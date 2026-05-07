"""ИУЛ v2 — PySide6 desktop app. Бизнес-логика идентична v1."""
import binascii
import gc
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pythoncom
import win32com.client

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QScrollArea, QFrame,
    QFileDialog, QDialog, QGridLayout, QProgressBar,
    QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QAbstractScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QPoint, QSize, QRect,
    QPropertyAnimation, QEasingCurve, QMimeData,
)
from PySide6.QtGui import (
    QFont, QColor, QIcon, QPixmap, QPainter, QCursor,
    QDragEnterEvent, QDropEvent, QMouseEvent, QPalette,
)

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------

if getattr(sys, "frozen", False):
    _BUNDLE_DIR = Path(sys._MEIPASS)
    USER_DATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "ИУЛ"
else:
    _BUNDLE_DIR = Path(__file__).resolve().parent
    USER_DATA_DIR = _BUNDLE_DIR

LOG_DIR        = USER_DATA_DIR / "Журналы"
CONFIG_PATH    = USER_DATA_DIR / "config.json"
TEMPLATE_PATH  = USER_DATA_DIR / "ИУЛ_шаблон.xlsx"
SIGNATURES_DIR = USER_DATA_DIR / "Подписи"


def init_user_data():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    for src, dst in [
        (_BUNDLE_DIR / "ИУЛ_шаблон.xlsx", TEMPLATE_PATH),
        (_BUNDLE_DIR / "config.json", CONFIG_PATH),
    ]:
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
    bundled_sigs = _BUNDLE_DIR / "Подписи"
    if bundled_sigs.exists() and not SIGNATURES_DIR.exists():
        shutil.copytree(bundled_sigs, SIGNATURES_DIR)


init_user_data()

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

EDITABLE_DIR_NAME = "ИУЛ_в_ред_формате"
MAX_FILES_PER_BATCH = 1000
MAX_OUTPUT_STEM = 140
ALLOWED_SECTION_CODES = {"ПЗУ", "АР", "КР", "ИОС"}
SIGNATURE_CELL_WIDTH_FACTOR  = 0.92
SIGNATURE_CELL_HEIGHT_FACTOR = 0.82
MIN_SIGNATURE_CELL_WIDTH  = 12
MIN_SIGNATURE_CELL_HEIGHT = 8

SECTION_NUMBERS = {"ПЗ": "1", "ПЗУ": "2", "АР": "3", "КР": "4", "ИОС": "5"}
SECTION_NAMES = {
    "ПЗУ": "Схема планировочной организации земельного участка",
    "АР":  "Архитектурные решения",
    "КР":  "Конструктивные решения",
    "ИОС": (
        "Сведения об инженерном оборудовании, о сетях инженерно-технического обеспечения, "
        "перечень инженерно-технических мероприятий, содержание технологических решений."
    ),
}
PART_NAMES = {
    ("АР", "1"): "Пояснительная записка",
    ("АР", "2"): "Блок А", ("АР", "3"): "Блок Б", ("АР", "4"): "Блок В",
    ("КР", "1"): "Блок А", ("КР", "2"): "Блок Б", ("КР", "3"): "Блок В",
    ("КР", "7"): "Подпорные стены",
    ("ИОС", "1"): "Внутреннее электрооборудование и электроосвещение",
    ("ИОС", "2"): "Система наружного электроснабжения и освещения",
}
BOOK_NAMES = {"1": "Блок А", "2": "Блок Б", "3": "Блок В"}
PEOPLE = {
    "Разработал":    {"АР": "Соколова М.В.",    "КР": "Иванов В.И.",      "ПЗУ": "Соколова М.В.",    "ИОС": "Барахович Ю.В."},
    "Проверил":      {"АР": "Герасимчук Е.И.",  "КР": "Герасимчук Е.И.", "ПЗУ": "Герасимчук Е.И.", "ИОС": "Иванов В.И."},
    "Нормоконтролер":{"АР": "Матинов С.А.",     "КР": "Матинов С.А.",    "ПЗУ": "Матинов С.А.",    "ИОС": "Матинов С.А."},
    "Утвердил":      {"АР": "Левченко А.И.",    "КР": "Левченко А.И.",   "ПЗУ": "Левченко А.И.",   "ИОС": "Левченко А.И."},
}
PROJECT_ROLE = {
    "АР": "Главный архитектор проекта", "КР": "Главный инженер проекта",
    "ПЗУ": "Главный архитектор проекта", "ИОС": "Главный инженер проекта",
}
SIGNATURE_PLACEHOLDERS = {
    "[Разработал_подпись]": "Разработал",
    "[Проверил_подпись]": "Проверил",
    "[Нормоконтролер_подпись]": "Нормоконтролер",
    "[Утвердил_подпись]": "Утвердил",
    "[Главный_проекта_фамилия_подпись]": "Утвердил",
}
CRITICAL_TEMPLATE_PLACEHOLDERS = {
    "[Номер_раздела]", "[Шифр_раздела]", "[Номер_папки]", "[Шифр_тома]",
    "[CRC_сумма]", "[Наименование_файла]", "[Дата_последнего_изменения]", "[Размер_файла]",
}
PROJECT_CODE = "1605-2022"


def load_config():
    if not CONFIG_PATH.exists():
        return
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    global PROJECT_CODE, SECTION_NUMBERS, SECTION_NAMES, PART_NAMES, BOOK_NAMES, PEOPLE, PROJECT_ROLE
    PROJECT_CODE = config.get("project_code", PROJECT_CODE)
    SECTION_NUMBERS.update(config.get("section_numbers", {}))
    SECTION_NAMES.update(config.get("section_names", {}))
    BOOK_NAMES.update(config.get("book_names", {}))
    PEOPLE.update(config.get("people", {}))
    PROJECT_ROLE.update(config.get("project_role", {}))
    part_names = {}
    for section_code, names in config.get("part_names", {}).items():
        for part_number, name in names.items():
            part_names[(section_code, str(part_number))] = name
    if part_names:
        PART_NAMES.update(part_names)


load_config()

REGISTERED_PLACEHOLDERS = set(CRITICAL_TEMPLATE_PLACEHOLDERS) | set(SIGNATURE_PLACEHOLDERS)

# ---------------------------------------------------------------------------
# Доменные классы
# ---------------------------------------------------------------------------

@dataclass
class ParsedName:
    section_number: str
    section_code: str
    subsection_number: str = ""
    part_number: str = ""
    book_number: str = ""
    warnings: list = field(default_factory=list)


@dataclass
class BuiltValues:
    values: dict
    parsed: ParsedName
    warnings: list = field(default_factory=list)

# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

def compact_number(value):
    return str(value).strip() if value is not None else ""

def normalize_spaces(value):
    return re.sub(r"\s+", " ", value).strip()

def normalize_file_text(value):
    text = value.replace("_", " ")
    text = re.sub(r"(?i)\b(?:nº|no|n)\s*(?=\d)", "№", text)
    text = re.sub(r"(?i)раздeл", "раздел", text)
    text = re.sub(r"П\s*Д\s*№", "ПД №", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*№\s*", " №", text)
    return normalize_spaces(text)

def format_bytes(size):
    return f"{size:,}".replace(",", " ")

def crc32_file(path):
    checksum = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            checksum = binascii.crc32(chunk, checksum)
    return f"{checksum & 0xFFFFFFFF:08X}"

def find_numbers(label, patterns, text, warnings):
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, text, re.IGNORECASE))
    normalized = [v for v in values if str(v).strip()]
    unique = []
    for v in normalized:
        if v not in unique:
            unique.append(v)
    if len(unique) > 1:
        warnings.append(f"Найдено несколько значений для поля '{label}': {', '.join(unique)}. Использую первое: {unique[0]}.")
    return unique[0] if unique else ""

def detect_section_code(text, warnings):
    upper = text.upper()
    matches = re.findall(r"(?<![А-ЯЁ])(ПЗУ|ИОС\s*\d*|АР|КР|ПЗ)(?![А-ЯЁ])", upper)
    normalized = []
    for match in matches:
        code = match.replace(" ", "")
        if code.startswith("ИОС"):
            code = "ИОС"
        if code not in normalized:
            normalized.append(code)
    supported   = [c for c in normalized if c in ALLOWED_SECTION_CODES]
    unsupported = [c for c in normalized if c not in ALLOWED_SECTION_CODES]
    if unsupported:
        warnings.append("Найден неподдерживаемый шифр раздела: " + ", ".join(unsupported) + ".")
    if not supported:
        possible = [t for t in re.findall(r"\b[А-ЯЁ]{2,5}\d*\b", upper)
                    if t not in {"ПД", "РАЗДЕЛ", "ЧАСТЬ", "КНИГА", "ПОДРАЗДЕЛ"}]
        if possible:
            warnings.append("Возможные неизвестные шифры в имени файла: " + ", ".join(possible) + ".")
    if len(supported) > 1:
        warnings.append(f"Найдено несколько шифров раздела: {', '.join(supported)}. Использую первый: {supported[0]}.")
    return supported[0] if supported else ""

def parse_file_name(path):
    stem = Path(path).stem
    warnings = []
    text = normalize_file_text(stem)
    section_code     = detect_section_code(text, warnings)
    section_number   = find_numbers("номер раздела",    [r"(?<!под)(?:раздел|разд[еe]л|р[аa]зд[еe]л)\s*пд\s*№?\s*(\d+)"], text, warnings)
    subsection_number= find_numbers("номер подраздела", [r"(?:подраздел|подр[аa]зд[еe]л)\s*пд\s*№?\s*(\d+)"], text, warnings)
    part_number      = find_numbers("номер части",      [r"част[ьи]\s*№?\s*(\d+)"], text, warnings)
    book_number      = find_numbers("номер книги",      [r"книг[аи]\s*№?\s*(\d+)"], text, warnings)
    if not section_code:
        details = " ".join(warnings)
        raise ValueError("не найден шифр раздела: ПЗУ, АР, КР или ИОС" + (f". {details}" if details else ""))
    if section_code not in ALLOWED_SECTION_CODES:
        raise ValueError(f"неподдерживаемый шифр раздела: {section_code}")
    if not section_number:
        section_number = SECTION_NUMBERS[section_code]
        warnings.append(f"Номер раздела не найден. Подставлен по шифру {section_code}: {section_number}.")
    if subsection_number and not section_number:
        raise ValueError("найден подраздел, но невозможно определить номер раздела")
    if book_number and not part_number:
        warnings.append("Найдена книга без части. Книга будет использована, но проверьте номер тома и шифр тома.")
    if section_code in {"АР", "КР", "ПЗУ"} and not part_number:
        warnings.append(f"Для раздела {section_code} не найден номер части. Номер папки будет только '{section_code}'.")
    if part_number and (section_code, part_number) not in PART_NAMES:
        warnings.append(f"Для раздела {section_code} и части {part_number} нет наименования части в правилах.")
    if book_number and book_number not in BOOK_NAMES:
        warnings.append(f"Для книги {book_number} нет наименования книги в правилах.")
    return ParsedName(
        section_number=section_number, section_code=section_code,
        subsection_number=subsection_number, part_number=part_number,
        book_number=book_number, warnings=warnings,
    )

def build_volume_number(parsed):
    base = parsed.subsection_number or parsed.section_number
    pieces = [base]
    if parsed.part_number:  pieces.append(parsed.part_number)
    if parsed.book_number:  pieces.append(parsed.book_number)
    return ".".join(pieces)

def build_folder_number(parsed):
    if parsed.section_code == "ИОС":
        return build_volume_number(parsed)
    return parsed.part_number

def build_volume_code(parsed):
    pieces = [f"{PROJECT_CODE}-{parsed.section_code}"]
    for v in (parsed.subsection_number, parsed.part_number, parsed.book_number):
        if v: pieces.append(v)
    return ".".join(pieces)

def clean_empty_lines(value):
    lines = []
    for line in str(value).splitlines():
        stripped = line.strip()
        if not re.sub(r"[\s.]+", "", stripped):
            continue
        lines.append(stripped)
    return "\n".join(lines)

def build_row2(parsed):
    values = [
        f"Раздел ПД №{parsed.section_number}",
        f"Подраздел ПД №{parsed.subsection_number}" if parsed.subsection_number else "",
        f"Часть №{parsed.part_number}" if parsed.part_number else "",
        f"Книга №{parsed.book_number}" if parsed.book_number else "",
        f"{parsed.section_code}{build_folder_number(parsed)}",
    ]
    return ", ".join([v for v in values if v])

def validate_source_file(path):
    warnings = []
    if not path.exists():
        raise ValueError("файл не найден")
    if not path.is_file():
        raise ValueError("выбранный путь не является файлом")
    if not path.suffix:
        warnings.append("У файла нет расширения.")
    elif path.suffix.lower() != ".pdf":
        warnings.append(f"Файл не PDF ({path.suffix}). Обработка продолжится.")
    try:
        with open(path, "rb") as f:
            f.read(1)
    except OSError as exc:
        raise ValueError(f"файл заблокирован: {exc}") from exc
    return warnings

def build_values(source_path, change_number="1", log=None):
    log = log or (lambda _: None)
    path = Path(source_path)
    warnings = []
    log("      Проверяю файл")
    warnings.extend(validate_source_file(path))
    log("      Парсю имя файла")
    parsed = parse_file_name(path)
    warnings.extend(parsed.warnings)
    log("      Читаю метаданные")
    try:
        stat = path.stat()
    except OSError as exc:
        raise ValueError(f"не удалось получить метаданные: {exc}") from exc
    try:
        modified = datetime.fromtimestamp(stat.st_mtime)
    except Exception:
        modified = datetime.now()
        warnings.append("Не удалось определить дату изменения файла.")
    log("      Считаю CRC32")
    try:
        crc = crc32_file(path)
    except OSError as exc:
        raise ValueError(f"CRC не посчиталась: {exc}") from exc
    section_code = parsed.section_code
    people = {role: PEOPLE[role].get(section_code, "") for role in PEOPLE}
    main_person = "Левченко А.И.\n(ПИ-059768)"
    values = {
        "[Номер_раздела]":          f"Раздел ПД №{parsed.section_number}",
        "[Номер_части]":            f"Часть №{parsed.part_number}" if parsed.part_number else "",
        "[Книга]":                  f"Книга №{parsed.book_number}" if parsed.book_number else "",
        "[Шифр_раздела]":           section_code,
        "[Номер_тома]":             build_volume_number(parsed),
        "[Номер_подраздела]":       f"Подраздел ПД №{parsed.subsection_number}" if parsed.subsection_number else "",
        "[Номер_раздела_2]":        f"Раздел {parsed.section_number}",
        "[Наименование_раздела]":   SECTION_NAMES.get(section_code, ""),
        "[Наименование_подраздела]":"Подраздел 1. Система электроснабжения" if section_code == "ИОС" else "",
        "[Номер_части_2]":          f"Часть {parsed.part_number}" if parsed.part_number else "",
        "[Наименование_части]":     PART_NAMES.get((section_code, parsed.part_number), "") if parsed.part_number else "",
        "[Номер_книги_2]":          f"Книга {parsed.book_number}" if parsed.book_number else "",
        "[Наименование_книги]":     BOOK_NAMES.get(parsed.book_number, "") if parsed.book_number else "",
        "[Шифр_тома]":              build_volume_code(parsed),
        "[Номер_папки]":            build_folder_number(parsed),
        "[Номер_изменения]":        change_number,
        "[CRC_сумма]":              crc,
        "[Наименование_файла]":     path.name,
        "[Дата_последнего_изменения]": modified.strftime("%d.%m.%Y"),
        "[Время_последнего_изменения]": modified.strftime("%H:%M"),
        "[Размер_файла]":           format_bytes(stat.st_size),
        "[Разработал]":             people["Разработал"],
        "[Проверил]":               people["Проверил"],
        "[Нормоконтролер]":         people["Нормоконтролер"],
        "[Утвердил]":               people["Утвердил"],
        "[Главный_проекта]":        PROJECT_ROLE.get(section_code, ""),
        "[Главный_проекта_фамилия]":main_person,
        "[Наименование_файла_УЛ]":  f"{path.name}_УЛ",
    }
    values["__row2__"]   = build_row2(parsed)
    values["__people__"] = people
    return BuiltValues(values=values, parsed=parsed, warnings=warnings)

def safe_output_name(source_path):
    name = Path(source_path).stem
    safe = re.sub(r'[<>:"/\\|?*]', "_", f"{name}_УЛ").strip(" .")
    if not safe:
        safe = "ИУЛ"
    if len(safe) > MAX_OUTPUT_STEM:
        digest = hashlib.sha1(safe.encode("utf-8", errors="ignore")).hexdigest()[:8]
        safe = f"{safe[:MAX_OUTPUT_STEM - 9]}_{digest}"
    return safe

def unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    for i in range(1, 1000):
        candidate = path.with_name(f"{path.stem}_{i}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise ValueError(f"не удалось подобрать свободное имя для {path.name}")

def find_signature(person_name):
    person_key = normalize_spaces(person_name).casefold()
    exact, surname_matches = [], []
    surname = person_name.split()[0].casefold() if person_name.split() else ""
    for path in SIGNATURES_DIR.glob("*.png"):
        stem_key = normalize_spaces(path.stem).casefold()
        if stem_key == person_key:
            exact.append(path)
        elif surname and stem_key.startswith(surname):
            surname_matches.append(path)
    if exact:
        return exact[0], ""
    if len(surname_matches) == 1:
        return surname_matches[0], f"Подпись для '{person_name}' найдена только по фамилии: {surname_matches[0].name}."
    if len(surname_matches) > 1:
        names = ", ".join(p.name for p in surname_matches)
        return None, f"Для '{person_name}' найдено несколько подписей по фамилии: {names}."
    return None, ""

def fit_picture_to_cell(sheet, cell, image_path):
    shape = sheet.Shapes.AddPicture(str(image_path), False, True, cell.Left, cell.Top, -1, -1)
    shape.LockAspectRatio = True
    max_w = cell.Width  * SIGNATURE_CELL_WIDTH_FACTOR
    max_h = cell.Height * SIGNATURE_CELL_HEIGHT_FACTOR
    warning = ""
    if max_w < MIN_SIGNATURE_CELL_WIDTH or max_h < MIN_SIGNATURE_CELL_HEIGHT:
        warning = f"Ячейка для подписи слишком маленькая: {cell.Address}."
    if shape.Width  > max_w: shape.Width  = max_w
    if shape.Height > max_h: shape.Height = max_h
    shape.Left = cell.Left + (cell.Width  - shape.Width)  / 2
    shape.Top  = cell.Top  + (cell.Height - shape.Height) / 2
    return warning

def replace_placeholders(workbook, values):
    warnings = []
    found = set()
    for sheet in workbook.Worksheets:
        used = sheet.UsedRange
        for row in range(1, used.Rows.Count + 1):
            for col in range(1, used.Columns.Count + 1):
                cell  = sheet.Cells(row, col)
                value = cell.Value2
                if not isinstance(value, str) or "[" not in value:
                    continue
                if "[Номер_папки]" in value and "[Номер_раздела]" in value and "[Шифр_раздела]" in value:
                    found.update(re.findall(r"\[[^\]]+\]", value))
                    cell.Value = values["__row2__"]
                    continue
                original = value
                for placeholder, role in SIGNATURE_PLACEHOLDERS.items():
                    if placeholder in original:
                        found.add(placeholder)
                        person = values["__people__"].get(role, "")
                        image_path, sig_warn = find_signature(person)
                        if sig_warn:
                            warnings.append(sig_warn)
                        cell.Value = original.replace(placeholder, "")
                        if image_path:
                            try:
                                w = fit_picture_to_cell(sheet, cell.MergeArea, image_path)
                                if w: warnings.append(w)
                            except Exception as exc:
                                warnings.append(f"Не удалось вставить подпись '{person}': {exc}.")
                        else:
                            warnings.append(f"Не найдена картинка подписи для '{person}'.")
                        original = cell.Value2 or ""
                for placeholder, replacement in values.items():
                    if not placeholder.startswith("["):
                        continue
                    if placeholder in original:
                        found.add(placeholder)
                    original = str(original).replace(placeholder, str(replacement))
                cell.Value = clean_empty_lines(original)
                cell.WrapText = True
    if not found:
        warnings.append("В шаблоне не найдено ни одного плейсхолдера.")
    missing = sorted(CRITICAL_TEMPLATE_PLACEHOLDERS - found)
    if missing:
        warnings.append("В шаблоне не найдены важные плейсхолдеры: " + ", ".join(missing) + ".")
    return warnings

def find_leftover_placeholders(workbook, known):
    leftovers = []
    for sheet in workbook.Worksheets:
        used = sheet.UsedRange
        for row in range(1, used.Rows.Count + 1):
            for col in range(1, used.Columns.Count + 1):
                v = sheet.Cells(row, col).Value2
                if not isinstance(v, str): continue
                remaining = [p for p in known if p in v]
                if remaining:
                    addr = sheet.Cells(row, col).Address(False, False)
                    leftovers.append(f"{sheet.Name}!{addr}: {', '.join(remaining)}")
    return leftovers

# ---------------------------------------------------------------------------
# Excel COM
# ---------------------------------------------------------------------------

class ExcelSession:
    def __init__(self):
        self.excel = None

    def __enter__(self):
        pythoncom.CoInitialize()
        self.excel = win32com.client.DispatchEx("Excel.Application")
        self.excel.Visible = False
        self.excel.DisplayAlerts = False
        self.excel.EnableEvents  = False
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.excel is not None:
                try:
                    try:
                        while self.excel.Workbooks.Count:
                            self.excel.Workbooks.Item(1).Close(SaveChanges=False)
                    except Exception:
                        pass
                    try:
                        self.excel.DisplayAlerts = False
                        self.excel.Quit()
                    except Exception:
                        pass
                finally:
                    self.excel = None
        finally:
            gc.collect()
            pythoncom.CoUninitialize()


def export_one(source_path, output_dir, change_number="1", session=None, log=None):
    log = log or (lambda _: None)
    if session is None:
        with ExcelSession() as s:
            return _export_one_inner(source_path, output_dir, change_number, s, log, owns_session=True)
    return _export_one_inner(source_path, output_dir, change_number, session, log, owns_session=False)


def _export_one_inner(source_path, output_dir, change_number, session, log, owns_session=False):
    source_path = Path(source_path).resolve()
    output_dir  = Path(output_dir).resolve()
    log("  1/12 Проверяю исходный файл")
    if not TEMPLATE_PATH.exists():
        raise ValueError(f"не найден шаблон: {TEMPLATE_PATH}")
    if not SIGNATURES_DIR.exists():
        raise ValueError(f"не найдена папка с подписями: {SIGNATURES_DIR}")
    log("  2/12 Разбираю название файла")
    built = build_values(source_path, change_number, log=log)
    values = built.values
    all_warnings = list(built.warnings)
    for w in built.warnings:
        log(f"      Предупреждение: {w}")
    if not build_volume_number(built.parsed):
        raise ValueError("невозможно собрать корректный номер тома")
    volume_code = build_volume_code(built.parsed)
    if ".." in volume_code or volume_code.endswith("."):
        raise ValueError(f"шифр тома собран некорректно: {volume_code}")
    log(f"      Раздел: {built.parsed.section_code}, часть: {built.parsed.part_number or '-'}")
    log(f"      Номер тома: {build_volume_number(built.parsed)}, шифр тома: {volume_code}")
    log("  3/12 Готовлю папки результата")
    editable_dir = output_dir / EDITABLE_DIR_NAME
    editable_dir.mkdir(parents=True, exist_ok=True)
    log("  4/12 Подбираю имена выходных файлов")
    base_name   = safe_output_name(source_path)
    desired_xlsx = (editable_dir / f"{base_name}.xlsx").resolve()
    desired_pdf  = (output_dir   / f"{base_name}.pdf").resolve()
    xlsx_path = unique_path(desired_xlsx)
    pdf_path  = unique_path(desired_pdf)
    log(f"      Excel: {xlsx_path.name}")
    log(f"      PDF:   {pdf_path.name}")
    log("  5/12 Копирую шаблон Excel")
    shutil.copy2(TEMPLATE_PATH, xlsx_path)
    workbook = None
    try:
        log("  6/12 Открываю Excel" if owns_session else "  6/12 Использую открытый Excel")
        log("  7/12 Открываю копию шаблона")
        workbook = session.excel.Workbooks.Open(str(xlsx_path))
        log("  8/12 Заменяю переменные и вставляю подписи")
        warnings = replace_placeholders(workbook, values)
        all_warnings.extend(warnings)
        for w in warnings:
            log(f"      Предупреждение: {w}")
        log("  9/12 Проверяю остатки плейсхолдеров")
        known = {k for k in values if k.startswith("[")} | set(SIGNATURE_PLACEHOLDERS)
        leftovers = find_leftover_placeholders(workbook, known)
        if leftovers:
            raise ValueError("после заполнения остались плейсхолдеры: " + "; ".join(leftovers[:10]))
        log("  10/12 Сохраняю Excel")
        workbook.Save()
        log("  11/12 Экспортирую PDF")
        workbook.ExportAsFixedFormat(0, str(pdf_path))
        log("  12/12 Закрываю книгу")
        return xlsx_path, pdf_path, all_warnings
    finally:
        if workbook is not None:
            workbook.Close(SaveChanges=False)

# ---------------------------------------------------------------------------
# Worker thread
# ---------------------------------------------------------------------------

class Worker(QThread):
    log_signal      = Signal(str, str)   # level, message
    progress_signal = Signal(int, int)   # current, total
    row_status      = Signal(int, str)   # file_index, status  ('processing'|'done'|'warning'|'error')
    done_signal     = Signal(int, int, int)  # ok, failed, warnings_count

    def __init__(self, files, output_dir, change_number, log_file_path, parent=None):
        super().__init__(parent)
        self.files         = files
        self.output_dir    = output_dir
        self.change_number = change_number
        self.log_file_path = log_file_path

    def _log(self, level, text):
        self.log_signal.emit(level, text)
        if self.log_file_path:
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(f"[{level.upper()}] {text}\n")
            except OSError:
                pass

    def run(self):
        ok = failed = warnings_count = 0
        total = len(self.files)
        try:
            self._log("info", f"Запуск Excel для пакетной обработки · {total} файлов")
            with ExcelSession() as session:
                for idx, file in enumerate(self.files):
                    self.row_status.emit(idx, "processing")
                    try:
                        self._log("info", f"")
                        self._log("info", f"[{idx+1}/{total}] {Path(file).name}")
                        xlsx_path, pdf_path, warns = export_one(
                            file, self.output_dir, self.change_number,
                            session=session, log=lambda t: self._log("info", t),
                        )
                        ok += 1
                        warnings_count += len(warns)
                        status = "warning" if warns else "done"
                        self.row_status.emit(idx, status)
                        self._log("success", f"Excel: {xlsx_path.name}")
                        self._log("success", f"PDF:   {pdf_path.name}")
                    except Exception as exc:
                        failed += 1
                        self.row_status.emit(idx, "error")
                        self._log("error", f"ОШИБКА: {exc}")
                        for line in traceback.format_exc().splitlines():
                            self._log("error", "  " + line)
                    self.progress_signal.emit(idx + 1, total)
        finally:
            self.done_signal.emit(ok, failed, warnings_count)

# ---------------------------------------------------------------------------
# Стили
# ---------------------------------------------------------------------------

BG        = "#0c0d0e"
BG1       = "#131516"
BG2       = "#1a1c1e"
BG3       = "#212427"
BORDER    = "#1e2024"
BORDER_S  = "#2a2b2d"
TEXT      = "#e8e9eb"
TEXT_S    = "#f5f6f7"
TEXT_M    = "#9ca0a8"
TEXT_F    = "#6b7079"
ACCENT    = "#3b82f6"
ACCENT_H  = "#4c8ff7"
GREEN     = "#22c55e"
AMBER     = "#f59e0b"
RED       = "#ef4444"
PURPLE    = "#a78bfa"

SECTION_COLORS = {"АР": "#fb923c", "КР": "#a78bfa", "ПЗУ": "#34d399", "ИОС": "#60a5fa"}

APP_QSS = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
    font-size: 13px;
    border: none;
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_S};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_F};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

QLineEdit {{
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 0 10px;
    color: {TEXT};
    height: 32px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
    background: {BG3};
}}
QTextEdit {{
    background: {BG};
    border: none;
    color: {TEXT_M};
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    padding: 4px 0;
}}
QPushButton {{
    background: {BG2};
    border: 1px solid {BORDER_S};
    border-radius: 7px;
    color: {TEXT};
    font-size: 13px;
    font-weight: 500;
    padding: 0 12px;
    height: 32px;
}}
QPushButton:hover {{
    background: {BG3};
    border-color: {TEXT_F};
}}
QPushButton:pressed {{
    background: {BG};
}}
QPushButton:disabled {{
    opacity: 0.45;
    color: {TEXT_F};
    background: {BG2};
    border-color: {BORDER};
}}
QPushButton#primary {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: white;
}}
QPushButton#primary:hover {{
    background: {ACCENT_H};
    border-color: {ACCENT_H};
}}
QPushButton#ghost {{
    background: transparent;
    border-color: transparent;
    color: {TEXT_M};
}}
QPushButton#ghost:hover {{
    background: rgba(255,255,255,20);
    color: {TEXT};
}}
QPushButton#icon_btn {{
    background: transparent;
    border: none;
    border-radius: 7px;
    color: {TEXT_M};
    width: 34px;
    height: 34px;
    padding: 0;
}}
QPushButton#icon_btn:hover {{
    background: rgba(255,255,255,15);
    color: {TEXT};
}}
QProgressBar {{
    background: {BG3};
    border: none;
    border-radius: 2px;
    height: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 2px;
}}
QTableWidget {{
    background: {BG1};
    border: 1px solid {BORDER};
    border-radius: 10px;
    gridline-color: {BORDER};
    outline: none;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background: rgba(59,130,246,0.15);
    color: {TEXT};
}}
QHeaderView::section {{
    background: {BG};
    color: {TEXT_F};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel#page_title {{
    font-size: 22px;
    font-weight: 600;
    color: {TEXT_S};
}}
QLabel#page_sub {{
    font-size: 13px;
    color: {TEXT_M};
}}
QLabel#section_label {{
    font-size: 11px;
    font-weight: 500;
    color: {TEXT_F};
    text-transform: uppercase;
    letter-spacing: 2px;
}}
QLabel#brand_title {{
    font-size: 14px;
    font-weight: 600;
    color: {TEXT_S};
}}
QLabel#brand_sub {{
    font-size: 11px;
    color: {TEXT_M};
    font-family: 'Cascadia Code', 'Consolas', monospace;
}}
QLabel#rail_label {{
    font-size: 11px;
    color: {TEXT_M};
    font-weight: 500;
}}
QLabel#rail_title {{
    font-size: 11px;
    font-weight: 500;
    color: {TEXT_F};
    text-transform: uppercase;
    letter-spacing: 2px;
}}
QFrame#topbar {{
    background: {BG1};
    border-bottom: 1px solid {BORDER};
}}
QFrame#titlebar {{
    background: transparent;
}}
QFrame#action_rail {{
    background: {BG};
    border-left: 1px solid {BORDER};
}}
QFrame#rail_section {{
    background: transparent;
    border-bottom: 1px solid {BORDER};
}}
QFrame#console_frame {{
    background: {BG1};
    border-top: 1px solid {BORDER};
}}
QFrame#file_list_frame {{
    background: {BG1};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#stat_card {{
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 12px;
}}
QFrame#drop_zone {{
    background: {BG1};
    border: 1.5px dashed {BORDER_S};
    border-radius: 14px;
}}
QFrame#drop_zone:hover {{
    border-color: {ACCENT};
    background: {BG2};
}}
"""

# ---------------------------------------------------------------------------
# Вспомогательные виджеты
# ---------------------------------------------------------------------------

def make_btn(text="", parent=None, kind="default", icon_char="", fixed_w=None):
    btn = QPushButton(text, parent)
    btn.setObjectName(kind if kind in ("primary", "ghost", "icon_btn") else "")
    if fixed_w:
        btn.setFixedWidth(fixed_w)
    if icon_char:
        btn.setText(icon_char + (" " + text if text else ""))
    return btn

def make_label(text, parent=None, obj_name=None, color=None, bold=False, size=None):
    lbl = QLabel(text, parent)
    if obj_name:
        lbl.setObjectName(obj_name)
    if color or bold or size:
        parts = []
        if color: parts.append(f"color: {color};")
        if bold:  parts.append("font-weight: 600;")
        if size:  parts.append(f"font-size: {size}px;")
        lbl.setStyleSheet(" ".join(parts))
    return lbl

def hline(parent=None):
    f = QFrame(parent)
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"background: {BORDER}; max-height: 1px; border: none;")
    return f

def status_pill(status: str) -> QLabel:
    MAP = {
        "idle":       ("В очереди",  TEXT_F,  BG3),
        "processing": ("Обработка",  ACCENT,  "#1a2847"),
        "done":       ("Готово",     GREEN,   "#0f2a1a"),
        "warning":    ("Предупр.",   AMBER,   "#2a200a"),
        "error":      ("Ошибка",     RED,     "#2a0f0f"),
    }
    label, fg, bg = MAP.get(status, MAP["idle"])
    lbl = QLabel(f"● {label}")
    lbl.setStyleSheet(
        f"color: {fg}; background: {bg}; border-radius: 999px; "
        f"padding: 2px 9px; font-size: 11px; font-weight: 500; "
        f"font-family: 'Cascadia Code','Consolas',monospace;"
    )
    lbl.setFixedHeight(22)
    return lbl

def section_tag(code: str) -> QLabel:
    color = SECTION_COLORS.get(code, TEXT_M)
    bg    = color + "1e"  # ~12% opacity hex trick
    lbl   = QLabel(code)
    lbl.setStyleSheet(
        f"color: {color}; background: {bg}; border-radius: 6px; "
        f"padding: 0 8px; font-size: 11px; font-weight: 500; "
        f"font-family: 'Cascadia Code','Consolas',monospace;"
    )
    lbl.setFixedHeight(22)
    return lbl

# ---------------------------------------------------------------------------
# TitleBar
# ---------------------------------------------------------------------------

class TitleBar(QFrame):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self._drag_pos = None
        self.setObjectName("titlebar")
        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 0, 0)
        layout.setSpacing(8)

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {ACCENT},stop:1 #60a5fa); border-radius: 4px;")

        title_lbl = QLabel("ИУЛ — Создание информационно-удостоверяющих листов")
        title_lbl.setStyleSheet(f"color: {TEXT_M}; font-size: 12px;")

        layout.addWidget(dot)
        layout.addWidget(title_lbl)
        layout.addStretch()

        for symbol, tip, slot in [("—", "Свернуть", window.showMinimized),
                                   ("□", "Развернуть", self._toggle_max),
                                   ("✕", "Закрыть",   window.close)]:
            btn = QPushButton(symbol)
            btn.setFixedSize(46, 36)
            btn.setToolTip(tip)
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; border: none; color: {TEXT_M}; font-size: 13px; }}"
                f"QPushButton:hover {{ background: rgba(255,255,255,20); color: {TEXT_S}; }}"
            )
            if symbol == "✕":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; border: none; color: {TEXT_M}; font-size: 13px; }}"
                    f"QPushButton:hover {{ background: #e81123; color: white; }}"
                )
            btn.clicked.connect(slot)
            layout.addWidget(btn)

    def _toggle_max(self):
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.window.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

# ---------------------------------------------------------------------------
# DropZone
# ---------------------------------------------------------------------------

class DropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("drop_zone")
        self.setAcceptDrops(True)
        self._compact = False
        self._build_ui()

    def _build_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(32, 40, 32, 40)
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setSpacing(0)

        icon_lbl = QLabel("⬆")
        icon_lbl.setFixedSize(52, 52)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"font-size: 24px; color: {ACCENT}; background: {BG3}; border-radius: 13px;"
        )

        title = make_label("Перетащите PDF-файлы сюда", color=TEXT_S, bold=True, size=15)
        title.setAlignment(Qt.AlignCenter)

        sub = make_label("либо нажмите, чтобы выбрать · поддерживается множественный выбор",
                         color=TEXT_M, size=12)
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)

        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        btn_row = QHBoxLayout(btn_container)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(8)
        btn_files  = make_btn("Выбрать файлы", kind="primary")
        btn_folder = make_btn("Открыть папку", kind="ghost")
        btn_files.clicked.connect(self._open_files)
        btn_folder.clicked.connect(self._open_folder)
        btn_row.addWidget(btn_files)
        btn_row.addWidget(btn_folder)

        hint = QLabel("Раздел ПД №N  ШифрРаздела  [часть №N]  [книга №N].pdf")
        hint.setStyleSheet(
            f"color: {TEXT_M}; font-size: 11px; font-family: 'Cascadia Code','Consolas',monospace; "
            f"background: {BG3}; border-radius: 999px; padding: 4px 12px;"
        )
        hint.setAlignment(Qt.AlignCenter)

        # Compact mode strip (hidden by default)
        compact_btn = make_btn("+ Добавить ещё файлы", kind="ghost")
        compact_btn.clicked.connect(self._open_files)
        compact_btn.hide()
        self._compact_btn = compact_btn

        self._full_widgets = [icon_lbl, title, sub, btn_container, hint]

        self._layout.addWidget(icon_lbl, alignment=Qt.AlignHCenter)
        self._layout.addSpacing(12)
        self._layout.addWidget(title)
        self._layout.addSpacing(4)
        self._layout.addWidget(sub)
        self._layout.addSpacing(14)
        self._layout.addWidget(btn_container)
        self._layout.addSpacing(14)
        self._layout.addWidget(hint, alignment=Qt.AlignHCenter)
        self._layout.addWidget(compact_btn, alignment=Qt.AlignCenter)

    def set_compact(self, compact: bool):
        if compact == self._compact:
            return
        self._compact = compact
        for w in self._full_widgets:
            w.setVisible(not compact)
        self._compact_btn.setVisible(compact)
        if compact:
            self._layout.setContentsMargins(12, 0, 12, 0)
            self.setFixedHeight(52)
        else:
            self._layout.setContentsMargins(32, 40, 32, 40)
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)

    def _open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Выберите PDF-файлы", "", "PDF файлы (*.pdf);;Все файлы (*)")
        if paths:
            self.files_dropped.emit(paths)

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с PDF-файлами")
        if folder:
            pdfs = [str(p) for p in Path(folder).glob("*.pdf")]
            if pdfs:
                self.files_dropped.emit(pdfs)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setStyleSheet(
                f"QFrame#drop_zone {{ background: rgba(59,130,246,0.1); "
                f"border: 1.5px solid {ACCENT}; border-radius: 14px; }}"
            )
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        paths = [u.toLocalFile() for u in event.mimeData().urls()
                 if u.toLocalFile().lower().endswith(".pdf") or "." not in Path(u.toLocalFile()).suffix]
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

# ---------------------------------------------------------------------------
# FileRowWidget
# ---------------------------------------------------------------------------

class FileRowWidget(QFrame):
    remove_requested = Signal(str)

    def __init__(self, file_path: str, parsed_summary: str, tag: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedHeight(58)
        self.setStyleSheet(
            f"QFrame {{ background: transparent; border-bottom: 1px solid {BORDER}; }}"
            f"QFrame:hover {{ background: rgba(255,255,255,10); }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(0)

        # Icon
        icon = QLabel("PDF")
        icon.setFixedSize(32, 32)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"background: {BG3}; border-radius: 7px; color: {RED}; "
            f"font-size: 9px; font-weight: 700; font-family: 'Cascadia Code','Consolas',monospace;"
        )
        layout.addWidget(icon)
        layout.addSpacing(10)

        # Name + meta
        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_col.setContentsMargins(0, 0, 0, 0)
        name = QLabel(Path(file_path).name)
        name.setStyleSheet(f"color: {TEXT_S}; font-size: 13px; font-weight: 500;")
        name.setMaximumWidth(400)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)
        stat_info = Path(file_path).stat() if Path(file_path).exists() else None
        size_str  = format_bytes(stat_info.st_size) if stat_info else "—"
        meta = QLabel(f"{size_str} bytes")
        meta.setStyleSheet(f"color: {TEXT_F}; font-size: 11px; font-family: 'Cascadia Code','Consolas',monospace;")
        meta_row.addWidget(meta)
        meta_row.addStretch()

        name_col.addWidget(name)
        name_col.addLayout(meta_row)
        layout.addLayout(name_col, 1)
        layout.addSpacing(16)

        # Section tag + label
        tag_col = QHBoxLayout()
        tag_col.setSpacing(8)
        tag_col.setContentsMargins(0, 0, 0, 0)
        stag = section_tag(tag)
        summary_lbl = QLabel(parsed_summary)
        summary_lbl.setStyleSheet(f"color: {TEXT_F}; font-size: 12px;")
        tag_col.addWidget(stag)
        tag_col.addWidget(summary_lbl)
        tag_col.addStretch()
        layout.addLayout(tag_col)
        layout.addSpacing(16)

        # Status pill (kept as attribute for updates)
        self._status_pill = status_pill("idle")
        layout.addWidget(self._status_pill)
        layout.addSpacing(8)

        # Remove button
        rm_btn = QPushButton("✕")
        rm_btn.setObjectName("icon_btn")
        rm_btn.setFixedSize(30, 30)
        rm_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {TEXT_F}; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: rgba(239,68,68,0.15); color: {RED}; }}"
        )
        rm_btn.clicked.connect(lambda: self.remove_requested.emit(self.file_path))
        layout.addWidget(rm_btn)

        # Progress bar (bottom edge, initially hidden)
        self._progress = QProgressBar(self)
        self._progress.setFixedHeight(2)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(
            f"QProgressBar {{ background: transparent; border: none; border-radius: 1px; }}"
            f"QProgressBar::chunk {{ background: {ACCENT}; border-radius: 1px; }}"
        )
        self._progress.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._progress.setGeometry(0, self.height() - 2, self.width(), 2)

    def set_status(self, status: str):
        MAP = {
            "idle":       ("● В очереди", TEXT_F, BG3),
            "processing": ("● Обработка", ACCENT, "#1a2847"),
            "done":       ("● Готово",    GREEN,  "#0f2a1a"),
            "warning":    ("● Предупр.",  AMBER,  "#2a200a"),
            "error":      ("● Ошибка",    RED,    "#2a0f0f"),
        }
        label, fg, bg = MAP.get(status, MAP["idle"])
        self._status_pill.setText(label)
        self._status_pill.setStyleSheet(
            f"color: {fg}; background: {bg}; border-radius: 999px; "
            f"padding: 2px 9px; font-size: 11px; font-weight: 500; "
            f"font-family: 'Cascadia Code','Consolas',monospace;"
        )
        if status == "processing":
            self._progress.setRange(0, 0)
            self._progress.show()
        else:
            self._progress.hide()

# ---------------------------------------------------------------------------
# ConsolePanel
# ---------------------------------------------------------------------------

class ConsolePanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("console_frame")
        self._open = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(36)
        self._header.setStyleSheet(
            f"QFrame {{ background: transparent; border-bottom: 1px solid {BORDER}; cursor: pointer; }}"
            f"QFrame:hover {{ background: rgba(255,255,255,10); }}"
        )
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(8)

        self._chev = QLabel("›")
        self._chev.setStyleSheet(f"color: {TEXT_M}; font-size: 16px; font-weight: 300;")
        self._chev.setFixedWidth(14)

        term_icon = QLabel("⊡")
        term_icon.setStyleSheet(f"color: {TEXT_M}; font-size: 12px;")

        title_lbl = QLabel("Журнал обработки")
        title_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px; font-weight: 500;")

        self._count_lbl = QLabel("0")
        self._count_lbl.setStyleSheet(
            f"color: {TEXT_F}; background: {BG3}; border-radius: 999px; "
            f"padding: 1px 7px; font-size: 10px; font-family: 'Cascadia Code','Consolas',monospace;"
        )

        header_layout.addWidget(self._chev)
        header_layout.addWidget(term_icon)
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(self._count_lbl)
        header_layout.addStretch()

        clr_btn = make_btn("Очистить", kind="ghost")
        clr_btn.setFixedHeight(24)
        clr_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {TEXT_F}; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {TEXT}; }}"
        )
        clr_btn.clicked.connect(self.clear)
        header_layout.addWidget(clr_btn)

        # Body
        self._body = QTextEdit()
        self._body.setReadOnly(True)
        self._body.setFixedHeight(200)
        self._body.setStyleSheet(
            f"QTextEdit {{ background: {BG}; border: none; color: {TEXT_M}; "
            f"font-family: 'Cascadia Code','Consolas',monospace; font-size: 12px; padding: 8px 16px; }}"
        )

        outer.addWidget(self._header)
        outer.addWidget(self._body)

        self._header.mousePressEvent = lambda _: self._toggle()
        self._log_count = 0

    def _toggle(self):
        self._open = not self._open
        self._body.setVisible(self._open)
        self._chev.setText("›" if not self._open else "⌄")

    def append(self, level: str, msg: str):
        colors = {"info": TEXT_M, "success": GREEN, "warn": AMBER, "error": RED}
        color  = colors.get(level, TEXT_M)
        ts     = datetime.now().strftime("%H:%M:%S")
        self._body.append(
            f'<span style="color:{TEXT_F};">{ts}</span>&nbsp;&nbsp;'
            f'<span style="color:{color};font-weight:500;">{level.upper():&lt;7}</span>&nbsp;&nbsp;'
            f'<span style="color:{TEXT};">{msg}</span>'
        )
        self._body.verticalScrollBar().setValue(self._body.verticalScrollBar().maximum())
        self._log_count += 1
        self._count_lbl.setText(str(self._log_count))

    def clear(self):
        self._body.clear()
        self._log_count = 0
        self._count_lbl.setText("0")

# ---------------------------------------------------------------------------
# ToastWidget
# ---------------------------------------------------------------------------

class ToastWidget(QFrame):
    def __init__(self, kind, title, msg, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet(
            f"QFrame {{ background: {BG2}; border: 1px solid {BORDER_S}; "
            f"border-radius: 10px; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icons   = {"success": ("✓", GREEN), "error": ("✕", RED),
                   "warn": ("!", AMBER),    "info":  ("i", ACCENT)}
        ch, col = icons.get(kind, ("i", ACCENT))
        icon_lbl = QLabel(ch)
        icon_lbl.setFixedSize(22, 22)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"color: {col}; background: rgba(0,0,0,0.3); border-radius: 6px; font-weight: 700;"
        )

        body = QVBoxLayout()
        body.setSpacing(1)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {TEXT_S}; font-size: 13px; font-weight: 500;")
        body.addWidget(t_lbl)
        if msg:
            m_lbl = QLabel(msg)
            m_lbl.setStyleSheet(f"color: {TEXT_M}; font-size: 12px;")
            m_lbl.setWordWrap(True)
            body.addWidget(m_lbl)

        layout.addWidget(icon_lbl)
        layout.addLayout(body, 1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(18, 18)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {TEXT_F}; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {TEXT}; }}"
        )
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)

# ---------------------------------------------------------------------------
# ActionRail
# ---------------------------------------------------------------------------

class ActionRail(QFrame):
    run_requested    = Signal()
    browse_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("action_rail")
        self.setFixedWidth(300)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Section: параметры выгрузки
        sec1 = QFrame()
        sec1.setObjectName("rail_section")
        s1l = QVBoxLayout(sec1)
        s1l.setContentsMargins(18, 16, 18, 16)
        s1l.setSpacing(12)
        s1l.addWidget(make_label("Параметры выгрузки", obj_name="rail_title"))

        f1 = QVBoxLayout()
        f1.setSpacing(4)
        f1.addWidget(make_label("Папка результата", obj_name="rail_label"))
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Выберите папку…")
        browse_btn = QPushButton("…")
        browse_btn.setFixedSize(32, 32)
        browse_btn.setToolTip("Выбрать папку")
        browse_btn.clicked.connect(self.browse_requested.emit)
        row1.addWidget(self._output_edit, 1)
        row1.addWidget(browse_btn)
        f1.addLayout(row1)

        f2 = QVBoxLayout()
        f2.setSpacing(4)
        f2.addWidget(make_label("Номер изменения", obj_name="rail_label"))
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self._revision_edit = QLineEdit("1")
        self._revision_edit.setFixedWidth(60)
        self._revision_edit.setAlignment(Qt.AlignCenter)
        self._revision_edit.setStyleSheet(
            f"QLineEdit {{ background: {BG2}; border: 1px solid {BORDER}; border-radius: 7px; "
            f"height: 32px; color: {TEXT}; font-family: 'Cascadia Code','Consolas',monospace; text-align: center; }}"
        )
        self._next_lbl = QLabel("следующий: 2")
        self._next_lbl.setStyleSheet(f"color: {TEXT_F}; font-size: 11px;")
        self._revision_edit.textChanged.connect(self._update_next)
        row2.addWidget(self._revision_edit)
        row2.addWidget(self._next_lbl)
        row2.addStretch()
        f2.addLayout(row2)

        s1l.addLayout(f1)
        s1l.addLayout(f2)

        # Section: сводка
        sec2 = QFrame()
        sec2.setObjectName("rail_section")
        s2l = QVBoxLayout(sec2)
        s2l.setContentsMargins(18, 16, 18, 16)
        s2l.setSpacing(10)
        s2l.addWidget(make_label("Сводка", obj_name="rail_title"))

        grid = QGridLayout()
        grid.setSpacing(8)
        self._stat_total  = self._make_stat("0", "в очереди")
        self._stat_done   = self._make_stat("0", "готово",   GREEN)
        self._stat_warn   = self._make_stat("0", "предупр.", AMBER)
        self._stat_err    = self._make_stat("0", "ошибки",   RED)
        grid.addWidget(self._stat_total[0], 0, 0)
        grid.addWidget(self._stat_done[0],  0, 1)
        grid.addWidget(self._stat_warn[0],  1, 0)
        grid.addWidget(self._stat_err[0],   1, 1)
        s2l.addLayout(grid)

        # Section: шаблон
        sec3 = QFrame()
        sec3.setObjectName("rail_section")
        sec3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        s3l = QVBoxLayout(sec3)
        s3l.setContentsMargins(18, 16, 18, 16)
        s3l.setSpacing(10)
        s3l.addWidget(make_label("Шаблон", obj_name="rail_title"))

        tmpl_frame = QFrame()
        tmpl_frame.setStyleSheet(
            f"QFrame {{ background: {BG2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}"
        )
        tfl = QHBoxLayout(tmpl_frame)
        tfl.setContentsMargins(10, 8, 10, 8)
        tfl.setSpacing(10)
        xlsx_icon = QLabel("XLSX")
        xlsx_icon.setFixedSize(28, 32)
        xlsx_icon.setAlignment(Qt.AlignCenter)
        xlsx_icon.setStyleSheet(
            f"background: rgba(34,197,94,0.15); border-radius: 5px; color: {GREEN}; "
            f"font-size: 9px; font-weight: 700; font-family: 'Cascadia Code','Consolas',monospace;"
        )
        tmpl_name = make_label("ИУЛ_шаблон.xlsx", color=TEXT_S, bold=False, size=12)
        tfl.addWidget(xlsx_icon)
        tfl.addWidget(tmpl_name, 1)
        s3l.addWidget(tmpl_frame)
        s3l.addStretch()

        # CTA
        cta_frame = QFrame()
        cta_frame.setStyleSheet(
            f"QFrame {{ background: {BG1}; border-top: 1px solid {BORDER}; }}"
        )
        ctal = QVBoxLayout(cta_frame)
        ctal.setContentsMargins(16, 14, 16, 14)
        ctal.setSpacing(8)

        self._run_btn = QPushButton("✦  Создать ИУЛ")
        self._run_btn.setObjectName("cta_btn")
        self._run_btn.setFixedHeight(48)
        self._run_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; border: none; border-radius: 10px; "
            f"color: white; font-size: 14px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {ACCENT_H}; }}"
            f"QPushButton:pressed {{ background: #2563eb; }}"
            f"QPushButton:disabled {{ background: {BG3}; color: {TEXT_F}; }}"
        )
        self._run_btn.clicked.connect(self.run_requested.emit)

        self._hint_lbl = QLabel("добавьте файлы, чтобы начать")
        self._hint_lbl.setAlignment(Qt.AlignCenter)
        self._hint_lbl.setStyleSheet(
            f"color: {TEXT_F}; font-size: 11px; "
            f"font-family: 'Cascadia Code','Consolas',monospace; background: transparent;"
        )
        ctal.addWidget(self._run_btn)
        ctal.addWidget(self._hint_lbl)

        outer.addWidget(sec1)
        outer.addWidget(sec2)
        outer.addWidget(sec3, 1)
        outer.addWidget(cta_frame)

    def _make_stat(self, val, label, color=None):
        card = QFrame()
        card.setObjectName("stat_card")
        card.setStyleSheet(
            f"QFrame {{ background: {BG2}; border: 1px solid {BORDER}; border-radius: 8px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(2)
        val_lbl = QLabel(val)
        val_lbl.setStyleSheet(
            f"color: {color or TEXT_S}; font-size: 18px; font-weight: 600; "
            f"font-family: 'Cascadia Code','Consolas',monospace; background: transparent;"
        )
        lbl_lbl = QLabel(label)
        lbl_lbl.setStyleSheet(f"color: {TEXT_M}; font-size: 11px; background: transparent;")
        cl.addWidget(val_lbl)
        cl.addWidget(lbl_lbl)
        return card, val_lbl

    def _update_next(self, text):
        try:
            n = int(text)
            self._next_lbl.setText(f"следующий: {n + 1}")
        except ValueError:
            self._next_lbl.setText("")

    def update_stats(self, total, done, warn, err):
        self._stat_total[1].setText(str(total))
        self._stat_done[1].setText(str(done))
        self._stat_warn[1].setText(str(warn))
        self._stat_err[1].setText(str(err))

    def set_running(self, running: bool, file_count: int = 0):
        if running:
            self._run_btn.setText("⏳  Обработка…")
            self._run_btn.setEnabled(False)
            self._hint_lbl.setText("не закрывайте окно")
        else:
            self._run_btn.setText("✦  Создать ИУЛ")
            self._run_btn.setEnabled(file_count > 0)
            self._hint_lbl.setText("добавьте файлы, чтобы начать" if file_count == 0 else "Ctrl+Enter чтобы запустить")

    @property
    def output_dir(self) -> str:
        return self._output_edit.text().strip()

    @output_dir.setter
    def output_dir(self, v: str):
        self._output_edit.setText(v)

    @property
    def revision(self) -> str:
        return self._revision_edit.text().strip() or "1"

# ---------------------------------------------------------------------------
# SettingsDialog
# ---------------------------------------------------------------------------

class SettingsDialog(QDialog):
    _ROLES    = ["Разработал", "Проверил", "Нормоконтролер", "Утвердил"]
    _SECTIONS = ["АР", "КР", "ПЗУ", "ИОС"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setWindowFlags(Qt.Dialog)
        self.resize(860, 600)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG1}; }}
            QWidget {{ background: {BG1}; color: {TEXT}; font-family: 'Segoe UI Variable Display','Segoe UI',sans-serif; font-size: 13px; border: none; }}
            QLineEdit {{ background: {BG2}; border: 1px solid {BORDER}; border-radius: 7px; padding: 0 10px; color: {TEXT}; height: 32px; }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
            QPushButton {{ background: {BG2}; border: 1px solid {BORDER_S}; border-radius: 7px; color: {TEXT}; font-size: 13px; font-weight: 500; padding: 0 12px; height: 32px; }}
            QPushButton:hover {{ background: {BG3}; }}
            QPushButton#primary {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
            QPushButton#primary:hover {{ background: {ACCENT_H}; }}
            QPushButton#ghost {{ background: transparent; border-color: transparent; color: {TEXT_M}; }}
            QPushButton#ghost:hover {{ background: rgba(255,255,255,20); color: {TEXT}; }}
            QTableWidget {{ background: {BG2}; border: 1px solid {BORDER}; border-radius: 8px; gridline-color: {BORDER}; outline: none; }}
            QTableWidget::item {{ padding: 6px 10px; border: none; color: {TEXT}; }}
            QTableWidget::item:selected {{ background: rgba(59,130,246,0.15); }}
            QHeaderView::section {{ background: {BG}; color: {TEXT_F}; border: none; border-bottom: 1px solid {BORDER}; padding: 8px 10px; font-size: 11px; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {BORDER_S}; border-radius: 4px; min-height: 30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self._build()

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet(
            f"QFrame {{ background: {BG}; border-right: 1px solid {BORDER}; }}"
        )
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(12, 16, 12, 16)
        sl.setSpacing(2)

        title_lbl = QLabel("Настройки")
        title_lbl.setStyleSheet(f"color: {TEXT_F}; font-size: 11px; font-weight: 500; padding: 4px 10px 8px;")
        sl.addWidget(title_lbl)

        self._tabs = []
        tab_defs = [
            ("project",    "▣  Проект"),
            ("persons",    "◎  Ответственные лица"),
            ("signatures", "✎  Подписи"),
            ("template",   "⊞  Шаблон"),
            ("system",     "⚙  Система"),
        ]
        for tab_id, label in tab_defs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; border: none; border-radius: 7px; "
                f"color: {TEXT_M}; font-size: 13px; font-weight: 500; "
                f"padding: 8px 10px; text-align: left; }}"
                f"QPushButton:hover {{ background: rgba(255,255,255,15); color: {TEXT}; }}"
                f"QPushButton:checked {{ background: {BG3}; color: {TEXT_S}; }}"
            )
            btn.clicked.connect(lambda checked, tid=tab_id: self._switch_tab(tid))
            sl.addWidget(btn)
            self._tabs.append((tab_id, btn))

        sl.addStretch()

        # Content
        content_frame = QFrame()
        content_frame.setStyleSheet("QFrame { background: transparent; }")
        cl = QVBoxLayout(content_frame)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet(f"QFrame {{ background: transparent; border-bottom: 1px solid {BORDER}; }}")
        hdrl = QHBoxLayout(hdr)
        hdrl.setContentsMargins(24, 0, 18, 0)
        self._hdr_title = QLabel("Проект")
        self._hdr_title.setStyleSheet(f"color: {TEXT_S}; font-size: 16px; font-weight: 600;")
        self._hdr_sub   = QLabel("Шифр и правила парсинга имён файлов")
        self._hdr_sub.setStyleSheet(f"color: {TEXT_M}; font-size: 12px;")
        htitles = QVBoxLayout()
        htitles.setSpacing(1)
        htitles.addWidget(self._hdr_title)
        htitles.addWidget(self._hdr_sub)
        hdrl.addLayout(htitles, 1)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {TEXT_M}; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: rgba(255,255,255,15); color: {TEXT}; }}"
        )
        close_btn.clicked.connect(self.reject)
        hdrl.addWidget(close_btn)

        # Stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QWidget { background: transparent; }")
        self._pages = {}
        for tab_id, _ in tab_defs:
            page = self._make_page(tab_id)
            self._stack.addWidget(page)
            self._pages[tab_id] = (self._stack.count() - 1, page)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(52)
        footer.setStyleSheet(f"QFrame {{ background: {BG}; border-top: 1px solid {BORDER}; }}")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(18, 0, 18, 0)
        fl.setSpacing(8)
        fl.addStretch()
        cancel_btn = make_btn("Отмена", kind="ghost")
        cancel_btn.clicked.connect(self.reject)
        save_btn = make_btn("Сохранить", kind="primary")
        save_btn.clicked.connect(self._save)
        fl.addWidget(cancel_btn)
        fl.addWidget(save_btn)

        cl.addWidget(hdr)
        cl.addWidget(self._stack, 1)
        cl.addWidget(footer)

        outer.addWidget(sidebar)
        outer.addWidget(content_frame, 1)

        self._switch_tab("project")

    def _make_page(self, tab_id):
        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget { background: transparent; }")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        if tab_id == "project":
            layout.addWidget(self._field("Шифр проекта", "project_code", PROJECT_CODE))
            hint = QLabel("Подставляется в ИУЛ как идентификатор объекта.")
            hint.setStyleSheet(f"color: {TEXT_F}; font-size: 11px;")
            layout.addWidget(hint)

        elif tab_id == "persons":
            info = QLabel("ФИО исполнителей по каждому разделу проекта.")
            info.setStyleSheet(f"color: {TEXT_F}; font-size: 11px;")
            layout.addWidget(info)

            table = QTableWidget(len(self._ROLES), len(self._SECTIONS) + 1)
            table.setHorizontalHeaderLabels(["Роль"] + self._SECTIONS)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            for c in range(1, len(self._SECTIONS) + 1):
                table.horizontalHeader().setSectionResizeMode(c, QHeaderView.Stretch)
            table.setSelectionMode(QAbstractScrollArea.NoSelection if hasattr(QAbstractScrollArea, "NoSelection") else table.NoSelection)
            table.setEditTriggers(QTableWidget.AllEditTriggers)
            self._people_table = table

            for r, role in enumerate(self._ROLES):
                table.setItem(r, 0, QTableWidgetItem(role))
                table.item(r, 0).setFlags(Qt.ItemIsEnabled)
                for c, sec in enumerate(self._SECTIONS, 1):
                    val = PEOPLE.get(role, {}).get(sec, "")
                    item = QTableWidgetItem(val)
                    table.setItem(r, c, item)
            layout.addWidget(table, 1)

        elif tab_id == "signatures":
            info = QLabel("PNG-подписи в папке Подписи/. Перетащите файлы или откройте папку.")
            info.setStyleSheet(f"color: {TEXT_F}; font-size: 11px;")
            info.setWordWrap(True)
            layout.addWidget(info)

            sigs = list(SIGNATURES_DIR.glob("*.png")) if SIGNATURES_DIR.exists() else []
            if sigs:
                for sig in sigs:
                    row = QFrame()
                    row.setStyleSheet(
                        f"QFrame {{ background: {BG2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}"
                    )
                    rl = QHBoxLayout(row)
                    rl.setContentsMargins(10, 6, 10, 6)
                    rl.addWidget(QLabel("🖊  " + sig.stem))
                    rl.addStretch()
                    layout.addWidget(row)
            else:
                empty = QLabel("Подписи не найдены. Поместите PNG-файлы в папку Подписи/.")
                empty.setStyleSheet(f"color: {TEXT_M}; font-size: 12px;")
                layout.addWidget(empty)

            open_btn = make_btn("Открыть папку Подписи ↗")
            open_btn.clicked.connect(lambda: os.startfile(str(SIGNATURES_DIR)) if SIGNATURES_DIR.exists() else None)
            layout.addWidget(open_btn)

        elif tab_id == "template":
            path_lbl = QLabel(str(TEMPLATE_PATH))
            path_lbl.setStyleSheet(
                f"color: {TEXT_M}; font-size: 12px; background: {BG2}; border: 1px solid {BORDER}; "
                f"border-radius: 7px; padding: 8px 12px; font-family: 'Cascadia Code','Consolas',monospace;"
            )
            path_lbl.setWordWrap(True)
            self._tmpl_path_lbl = path_lbl
            layout.addWidget(path_lbl)

            open_btn = make_btn("Открыть шаблон в Excel ↗")
            open_btn.clicked.connect(self._open_template)
            replace_btn = make_btn("Заменить шаблон…")
            replace_btn.clicked.connect(self._replace_template)
            btn_row = QHBoxLayout()
            btn_row.addWidget(open_btn)
            btn_row.addWidget(replace_btn)
            btn_row.addStretch()
            layout.addLayout(btn_row)

        elif tab_id == "system":
            items = [
                ("Microsoft Excel",   "через WIN32 COM",               "✓ Требуется"),
                ("Папка данных",      str(USER_DATA_DIR),              ""),
                ("Папка журналов",    str(LOG_DIR),                    ""),
                ("config.json",       str(CONFIG_PATH),                "✓ Найден" if CONFIG_PATH.exists() else "✕ Не найден"),
                ("Шаблон .xlsx",      str(TEMPLATE_PATH),              "✓ Найден" if TEMPLATE_PATH.exists() else "✕ Не найден"),
            ]
            for name, detail, status in items:
                row = QFrame()
                row.setStyleSheet(
                    f"QFrame {{ background: {BG2}; border: 1px solid {BORDER}; border-radius: 8px; }}"
                )
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 8, 12, 8)
                rl.setSpacing(12)
                name_lbl = QLabel(name)
                name_lbl.setStyleSheet(f"color: {TEXT_S}; font-weight: 500; font-size: 13px;")
                name_lbl.setFixedWidth(130)
                detail_lbl = QLabel(detail)
                detail_lbl.setStyleSheet(
                    f"color: {TEXT_F}; font-size: 11px; font-family: 'Cascadia Code','Consolas',monospace;"
                )
                rl.addWidget(name_lbl)
                rl.addWidget(detail_lbl, 1)
                if status:
                    ok = status.startswith("✓")
                    s_lbl = QLabel(status)
                    s_lbl.setStyleSheet(f"color: {GREEN if ok else RED}; font-size: 12px; font-weight: 500;")
                    rl.addWidget(s_lbl)
                layout.addWidget(row)

            open_logs_btn = make_btn("Открыть папку журналов ↗")
            open_logs_btn.clicked.connect(lambda: os.startfile(str(LOG_DIR)) if LOG_DIR.exists() else None)
            layout.addWidget(open_logs_btn)

        layout.addStretch()
        return wrapper

    def _field(self, label, attr_name, default=""):
        frame = QFrame()
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(6)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px; font-weight: 500;")
        edit = QLineEdit(default)
        edit.setObjectName(f"field_{attr_name}")
        fl.addWidget(lbl)
        fl.addWidget(edit)
        setattr(self, f"_edit_{attr_name}", edit)
        return frame

    def _switch_tab(self, tab_id):
        headers = {
            "project":    ("Проект",               "Шифр и правила парсинга"),
            "persons":    ("Ответственные лица",    "ФИО исполнителей по разделам"),
            "signatures": ("Подписи",               "PNG-подписи и автосопоставление"),
            "template":   ("Шаблон Excel",          "Заменить или восстановить шаблон"),
            "system":     ("Система",               "Хранилище, диагностика, журналы"),
        }
        h, s = headers.get(tab_id, ("", ""))
        self._hdr_title.setText(h)
        self._hdr_sub.setText(s)
        idx, _ = self._pages[tab_id]
        self._stack.setCurrentIndex(idx)
        for tid, btn in self._tabs:
            btn.setChecked(tid == tab_id)

    def _open_template(self):
        if TEMPLATE_PATH.exists():
            os.startfile(str(TEMPLATE_PATH))

    def _replace_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите новый шаблон", "", "Excel файлы (*.xlsx);;Все файлы (*)"
        )
        if not path:
            return
        try:
            shutil.copy2(path, TEMPLATE_PATH)
            self._tmpl_path_lbl.setText(str(TEMPLATE_PATH))
            QMessageBox.information(self, "Шаблон заменён", "Новый шаблон скопирован.")
        except OSError as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось скопировать шаблон:\n{exc}")

    def _save(self):
        config = {}
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass

        if hasattr(self, "_edit_project_code"):
            config["project_code"] = self._edit_project_code.text().strip()

        if hasattr(self, "_people_table"):
            people = {}
            for r, role in enumerate(self._ROLES):
                people[role] = {}
                for c, sec in enumerate(self._SECTIONS, 1):
                    item = self._people_table.item(r, c)
                    people[role][sec] = item.text().strip() if item else ""
            config["people"] = people

        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки:\n{exc}")
            return

        load_config()
        self.accept()
        QMessageBox.information(self.parent(), "Настройки", "Настройки сохранены и применены.")

# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class IULMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ИУЛ")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(1140, 720)
        self.setMinimumSize(900, 600)

        self._files: list[str] = []         # file paths
        self._file_rows: list[FileRowWidget] = []
        self._worker: Worker | None = None
        self._log_file_path: Path | None = None
        self._stats = {"total": 0, "done": 0, "warn": 0, "err": 0}

        self._build_ui()
        self.setStyleSheet(APP_QSS)

    # ---- UI construction ----

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Title bar
        self._titlebar = TitleBar(self)
        root_layout.addWidget(self._titlebar)

        # Top bar
        topbar = self._make_topbar()
        root_layout.addWidget(topbar)

        # Body
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Main pane
        main_pane = QWidget()
        main_pane_layout = QVBoxLayout(main_pane)
        main_pane_layout.setContentsMargins(0, 0, 0, 0)
        main_pane_layout.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet(f"background: {BG};")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(32, 28, 32, 20)
        self._content_layout.setSpacing(0)

        # Page title
        self._content_layout.addWidget(make_label("Создание информационно-удостоверяющих листов", obj_name="page_title"))
        self._content_layout.addSpacing(4)
        self._content_layout.addWidget(make_label(
            "Загрузите PDF-файлы — приложение распарсит имя, рассчитает CRC32, заполнит шаблон Excel и экспортирует ИУЛ.",
            obj_name="page_sub"
        ))
        self._content_layout.addSpacing(20)

        # Drop zone
        self._drop_zone = DropZone()
        self._drop_zone.files_dropped.connect(self._on_files_dropped)
        self._content_layout.addWidget(self._drop_zone)
        self._content_layout.addSpacing(20)

        # File list area (initially hidden)
        self._file_list_header = self._make_file_list_header()
        self._file_list_header.hide()
        self._content_layout.addWidget(self._file_list_header)
        self._content_layout.addSpacing(6)

        self._file_list_frame = QFrame()
        self._file_list_frame.setObjectName("file_list_frame")
        self._file_list_layout = QVBoxLayout(self._file_list_frame)
        self._file_list_layout.setContentsMargins(0, 0, 0, 0)
        self._file_list_layout.setSpacing(0)

        # Header row
        hdr_row = QFrame()
        hdr_row.setStyleSheet(f"background: {BG}; border-bottom: 1px solid {BORDER};")
        hdr_row.setFixedHeight(36)
        hdr_rl = QHBoxLayout(hdr_row)
        hdr_rl.setContentsMargins(14, 0, 14, 0)
        for txt, stretch in [("Файл", 1), ("Раздел / Часть", 0), ("Статус", 0), ("", 0)]:
            lbl = QLabel(txt)
            lbl.setStyleSheet(
                f"color: {TEXT_F}; font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; background: transparent;"
            )
            if stretch:
                hdr_rl.addWidget(lbl, 1)
            else:
                lbl.setFixedWidth(140 if txt == "Раздел / Часть" else (120 if txt == "Статус" else 40))
                hdr_rl.addWidget(lbl)

        self._file_list_layout.addWidget(hdr_row)
        self._file_list_frame.hide()
        self._content_layout.addWidget(self._file_list_frame)

        # Warning/error banner
        self._banner = QLabel("")
        self._banner.hide()
        self._banner.setWordWrap(True)
        self._content_layout.addWidget(self._banner)

        self._content_layout.addStretch()

        scroll.setWidget(content)
        main_pane_layout.addWidget(scroll, 1)

        # Progress bar
        self._global_progress = QProgressBar()
        self._global_progress.setFixedHeight(3)
        self._global_progress.setTextVisible(False)
        self._global_progress.hide()
        main_pane_layout.addWidget(self._global_progress)

        # Console
        self._console = ConsolePanel()
        main_pane_layout.addWidget(self._console)

        # Action rail
        self._rail = ActionRail()
        self._rail.run_requested.connect(self._run)
        self._rail.browse_requested.connect(self._browse_output)

        body_layout.addWidget(main_pane, 1)
        body_layout.addWidget(self._rail)

        root_layout.addWidget(body, 1)

        # Toast container (absolute)
        self._toasts: list[ToastWidget] = []

    def _make_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)

        brand_mark = QLabel("ИУЛ")
        brand_mark.setFixedSize(32, 32)
        brand_mark.setAlignment(Qt.AlignCenter)
        brand_mark.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {ACCENT},stop:0.5 #60a5fa,stop:1 {PURPLE}); "
            f"border-radius: 8px; color: white; font-size: 12px; font-weight: 700;"
        )

        brand_meta = QVBoxLayout()
        brand_meta.setSpacing(1)
        brand_meta.addWidget(make_label("Создание ИУЛ", obj_name="brand_title"))
        self._brand_sub = make_label(f"проект {PROJECT_CODE} · ревизия 1", obj_name="brand_sub")
        brand_meta.addWidget(self._brand_sub)

        layout.addWidget(brand_mark)
        layout.addLayout(brand_meta)
        layout.addStretch()

        settings_btn = make_btn("", kind="icon_btn", icon_char="⚙")
        settings_btn.setFixedSize(34, 34)
        settings_btn.setToolTip("Настройки")
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)

        return bar

    def _make_file_list_header(self):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        section_lbl = QLabel("Очередь обработки")
        section_lbl.setObjectName("section_label")
        self._count_lbl = QLabel("0")
        self._count_lbl.setStyleSheet(
            f"background: {BG3}; color: {TEXT_M}; border-radius: 999px; "
            f"padding: 1px 7px; font-size: 10px; font-family: 'Cascadia Code','Consolas',monospace;"
        )
        layout.addWidget(section_lbl)
        layout.addWidget(self._count_lbl)
        layout.addStretch()

        clear_btn = make_btn("✕  Очистить", kind="ghost")
        clear_btn.clicked.connect(self._clear_files)
        layout.addWidget(clear_btn)

        return frame

    # ---- File management ----

    def _on_files_dropped(self, paths: list[str]):
        added = 0
        for path in paths:
            if path not in self._files:
                if len(self._files) >= MAX_FILES_PER_BATCH:
                    self._toast("warn", "Слишком много файлов",
                                f"Максимум {MAX_FILES_PER_BATCH} файлов за раз.")
                    break
                self._files.append(path)
                self._add_file_row(path)
                added += 1

        if added:
            self._refresh_list_visibility()
            if not self._rail.output_dir:
                self._rail.output_dir = str(Path(self._files[0]).parent)
            self._toast("success", f"Добавлено {added} файлов", "Готовы к обработке.")
            self._console.append("info", f"Добавлено {added} файлов в очередь")
            self._update_stats()

    def _add_file_row(self, path: str):
        try:
            parsed = parse_file_name(path)
            parts = [parsed.section_code]
            if parsed.part_number:  parts.append(f"Ч.{parsed.part_number}")
            if parsed.book_number:  parts.append(f"Кн.{parsed.book_number}")
            summary = " · ".join(parts[1:]) if len(parts) > 1 else ""
            tag     = parsed.section_code
        except Exception:
            summary = "ошибка парсинга"
            tag     = ""

        row = FileRowWidget(path, summary, tag)
        row.remove_requested.connect(self._remove_file)
        self._file_rows.append(row)
        self._file_list_layout.addWidget(row)

    def _remove_file(self, path: str):
        if self._worker and self._worker.isRunning():
            return
        idx = next((i for i, p in enumerate(self._files) if p == path), None)
        if idx is None:
            return
        self._files.pop(idx)
        row = self._file_rows.pop(idx)
        row.deleteLater()
        self._refresh_list_visibility()
        self._update_stats()

    def _clear_files(self):
        if self._worker and self._worker.isRunning():
            return
        self._files.clear()
        for row in self._file_rows:
            row.deleteLater()
        self._file_rows.clear()
        self._refresh_list_visibility()
        self._update_stats()

    def _refresh_list_visibility(self):
        has = len(self._files) > 0
        self._file_list_header.setVisible(has)
        self._file_list_frame.setVisible(has)
        self._count_lbl.setText(str(len(self._files)))
        self._drop_zone.set_compact(has)
        self._rail.set_running(False, len(self._files))

    def _update_stats(self):
        total = len(self._files)
        done  = sum(1 for r in self._file_rows if hasattr(r, "_current_status") and r._current_status == "done")
        warn  = sum(1 for r in self._file_rows if hasattr(r, "_current_status") and r._current_status == "warning")
        err   = sum(1 for r in self._file_rows if hasattr(r, "_current_status") and r._current_status == "error")
        self._rail.update_stats(total, done, warn, err)

    # ---- Actions ----

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Куда сохранить ИУЛ")
        if folder:
            self._rail.output_dir = folder

    def _show_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        # Update brand subtitle with potentially changed project code
        self._brand_sub.setText(f"проект {PROJECT_CODE} · ревизия {self._rail.revision}")

    # ---- Run ----

    def _run(self):
        if not TEMPLATE_PATH.exists():
            QMessageBox.critical(self, "Ошибка", f"Не найден шаблон:\n{TEMPLATE_PATH}")
            return
        if not self._files:
            QMessageBox.warning(self, "Нет файлов", "Добавьте один или несколько файлов.")
            return
        output_dir = self._rail.output_dir
        if not output_dir:
            QMessageBox.warning(self, "Нет папки", "Выберите папку результата.")
            return
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "Ошибка папки", f"Не удалось создать папку результата:\n{exc}")
            return

        # Reset statuses
        for row in self._file_rows:
            row.set_status("idle")
            row._current_status = "idle"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_file_path = LOG_DIR / f"ИУЛ_журнал_{timestamp}.txt"

        self._global_progress.setRange(0, len(self._files))
        self._global_progress.setValue(0)
        self._global_progress.show()
        self._rail.set_running(True)

        self._console.append("info", f"Старт · {len(self._files)} файлов · {output_dir}")

        self._worker = Worker(
            files         = list(self._files),
            output_dir    = output_dir,
            change_number = self._rail.revision,
            log_file_path = self._log_file_path,
        )
        self._worker.log_signal.connect(self._on_log)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.row_status.connect(self._on_row_status)
        self._worker.done_signal.connect(self._on_done)
        self._worker.start()

    # ---- Worker signals ----

    def _on_log(self, level: str, msg: str):
        if msg.strip():
            self._console.append(level, msg)

    def _on_progress(self, current: int, total: int):
        self._global_progress.setValue(current)

    def _on_row_status(self, idx: int, status: str):
        if 0 <= idx < len(self._file_rows):
            self._file_rows[idx].set_status(status)
            self._file_rows[idx]._current_status = status
        self._update_stats()

    def _on_done(self, ok: int, failed: int, warnings_count: int):
        self._global_progress.hide()
        self._rail.set_running(False, len(self._files))
        self._update_stats()

        if failed == 0:
            self._toast("success", "Обработка завершена",
                        f"Создано: {ok}  · предупреждений: {warnings_count}")
            self._console.append("success", f"Готово · создано: {ok}, предупреждений: {warnings_count}")
        else:
            self._toast("warn", "Обработка завершена с ошибками",
                        f"Создано: {ok}  · ошибок: {failed}  · предупреждений: {warnings_count}")
            self._console.append("warn", f"Завершено · создано: {ok}, ошибок: {failed}")

    # ---- Toasts ----

    def _toast(self, kind: str, title: str, msg: str = ""):
        toast = ToastWidget(kind, title, msg, self)
        # Position in top-right
        toast.show()
        toast.adjustSize()
        self._toasts.append(toast)
        self._restack_toasts()
        QTimer.singleShot(4500, lambda: self._remove_toast(toast))

    def _restack_toasts(self):
        y = 70
        for t in self._toasts:
            if not t.isHidden():
                t.move(self.width() - t.width() - 20, y)
                y += t.height() + 8

    def _remove_toast(self, toast: ToastWidget):
        if toast in self._toasts:
            self._toasts.remove(toast)
        toast.deleteLater()
        self._restack_toasts()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._restack_toasts()

    def keyPressEvent(self, event):
        if (event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_Return:
            self._run()
        super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not sys.platform.startswith("win"):
        raise RuntimeError("Программа рассчитана на Windows с установленным Microsoft Excel.")

    app = QApplication(sys.argv)
    app.setApplicationName("ИУЛ")
    app.setStyle("Fusion")

    # Dark palette base so native controls inherit it
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base,            QColor(BG2))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG1))
    palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button,          QColor(BG2))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    win = IULMainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
