import binascii
import gc
import hashlib
import json
import os
import queue
import re
import shutil
import sys
import threading
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import (
    BOTH, END, LEFT, RIGHT, X, DISABLED, NORMAL,
    StringVar, Text, Tk, Toplevel, filedialog, messagebox,
)
from tkinter import ttk

import pythoncom
import win32com.client


# ---------------------------------------------------------------------------
# Пути: в frozen-режиме данные хранятся в %APPDATA%\ИУЛ (невидимо для юзера)
# ---------------------------------------------------------------------------

if getattr(sys, "frozen", False):
    _BUNDLE_DIR = Path(sys._MEIPASS)
    USER_DATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "ИУЛ"
else:
    _BUNDLE_DIR = Path(__file__).resolve().parent
    USER_DATA_DIR = _BUNDLE_DIR  # в dev-режиме данные лежат прямо в папке проекта

LOG_DIR = USER_DATA_DIR / "Журналы"
CONFIG_PATH = USER_DATA_DIR / "config.json"
TEMPLATE_PATH = USER_DATA_DIR / "ИУЛ_шаблон.xlsx"
SIGNATURES_DIR = USER_DATA_DIR / "Подписи"


def init_user_data():
    """Копирует данные из bundle в USER_DATA_DIR (только если их там ещё нет)."""
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
# Константы и словари (используются как дефолты; config.json переопределяет)
# ---------------------------------------------------------------------------

EDITABLE_DIR_NAME = "ИУЛ_в_ред_формате"
MAX_FILES_PER_BATCH = 1000
MAX_OUTPUT_STEM = 140
ALLOWED_SECTION_CODES = {"ПЗУ", "АР", "КР", "ИОС"}
SIGNATURE_CELL_WIDTH_FACTOR = 0.92
SIGNATURE_CELL_HEIGHT_FACTOR = 0.82
MIN_SIGNATURE_CELL_WIDTH = 12
MIN_SIGNATURE_CELL_HEIGHT = 8

SECTION_NUMBERS = {
    "ПЗ": "1",
    "ПЗУ": "2",
    "АР": "3",
    "КР": "4",
    "ИОС": "5",
}

SECTION_NAMES = {
    "ПЗУ": "Схема планировочной организации земельного участка",
    "АР": "Архитектурные решения",
    "КР": "Конструктивные решения",
    "ИОС": (
        "Сведения об инженерном оборудовании, о сетях инженерно-технического обеспечения, "
        "перечень инженерно-технических мероприятий, содержание технологических решений."
    ),
}

PART_NAMES = {
    ("АР", "1"): "Пояснительная записка",
    ("АР", "2"): "Блок А",
    ("АР", "3"): "Блок Б",
    ("АР", "4"): "Блок В",
    ("КР", "1"): "Блок А",
    ("КР", "2"): "Блок Б",
    ("КР", "3"): "Блок В",
    ("КР", "7"): "Подпорные стены",
    ("ИОС", "1"): "Внутреннее электрооборудование и электроосвещение",
    ("ИОС", "2"): "Система наружного электроснабжения и освещения",
}

BOOK_NAMES = {
    "1": "Блок А",
    "2": "Блок Б",
    "3": "Блок В",
}

PEOPLE = {
    "Разработал": {
        "АР": "Соколова М.В.",
        "КР": "Иванов В.И.",
        "ПЗУ": "Соколова М.В.",
        "ИОС": "Барахович Ю.В.",
    },
    "Проверил": {
        "АР": "Герасимчук Е.И.",
        "КР": "Герасимчук Е.И.",
        "ПЗУ": "Герасимчук Е.И.",
        "ИОС": "Иванов В.И.",
    },
    "Нормоконтролер": {
        "АР": "Матинов С.А.",
        "КР": "Матинов С.А.",
        "ПЗУ": "Матинов С.А.",
        "ИОС": "Матинов С.А.",
    },
    "Утвердил": {
        "АР": "Левченко А.И.",
        "КР": "Левченко А.И.",
        "ПЗУ": "Левченко А.И.",
        "ИОС": "Левченко А.И.",
    },
}

PROJECT_ROLE = {
    "АР": "Главный архитектор проекта",
    "КР": "Главный инженер проекта",
    "ПЗУ": "Главный архитектор проекта",
    "ИОС": "Главный инженер проекта",
}

SIGNATURE_PLACEHOLDERS = {
    "[Разработал_подпись]": "Разработал",
    "[Проверил_подпись]": "Проверил",
    "[Нормоконтролер_подпись]": "Нормоконтролер",
    "[Утвердил_подпись]": "Утвердил",
    "[Главный_проекта_фамилия_подпись]": "Утвердил",
}

CRITICAL_TEMPLATE_PLACEHOLDERS = {
    "[Номер_раздела]",
    "[Шифр_раздела]",
    "[Номер_папки]",
    "[Шифр_тома]",
    "[CRC_сумма]",
    "[Наименование_файла]",
    "[Дата_последнего_изменения]",
    "[Размер_файла]",
}

PROJECT_CODE = "1605-2022"


def load_config():
    if not CONFIG_PATH.exists():
        return
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

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
    warnings: list[str] = field(default_factory=list)


@dataclass
class BuiltValues:
    values: dict
    parsed: ParsedName
    warnings: list[str] = field(default_factory=list)


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
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            checksum = binascii.crc32(chunk, checksum)
    return f"{checksum & 0xFFFFFFFF:08X}"


def find_numbers(label, patterns, text, warnings):
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, text, re.IGNORECASE))
    normalized = [value for value in values if str(value).strip()]
    unique = []
    for value in normalized:
        if value not in unique:
            unique.append(value)
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

    supported = [code for code in normalized if code in ALLOWED_SECTION_CODES]
    unsupported = [code for code in normalized if code not in ALLOWED_SECTION_CODES]
    if unsupported:
        warnings.append("Найден неподдерживаемый шифр раздела: " + ", ".join(unsupported) + ".")
    if not supported:
        possible_codes = [
            token for token in re.findall(r"\b[А-ЯЁ]{2,5}\d*\b", upper)
            if token not in {"ПД", "РАЗДЕЛ", "ЧАСТЬ", "КНИГА", "ПОДРАЗДЕЛ"}
        ]
        if possible_codes:
            warnings.append("Возможные неизвестные шифры в имени файла: " + ", ".join(possible_codes) + ".")
    if len(supported) > 1:
        warnings.append(f"Найдено несколько шифров раздела: {', '.join(supported)}. Использую первый: {supported[0]}.")
    return supported[0] if supported else ""


def parse_file_name(path):
    stem = Path(path).stem
    warnings = []
    text = normalize_file_text(stem)

    section_code = detect_section_code(text, warnings)
    section_number = find_numbers(
        "номер раздела",
        [r"(?<!под)(?:раздел|разд[еe]л|р[аa]зд[еe]л)\s*пд\s*№?\s*(\d+)"],
        text,
        warnings,
    )
    subsection_number = find_numbers(
        "номер подраздела",
        [r"(?:подраздел|подр[аa]зд[еe]л)\s*пд\s*№?\s*(\d+)"],
        text,
        warnings,
    )
    part_number = find_numbers(
        "номер части",
        [r"част[ьи]\s*№?\s*(\d+)"],
        text,
        warnings,
    )
    book_number = find_numbers(
        "номер книги",
        [r"книг[аи]\s*№?\s*(\d+)"],
        text,
        warnings,
    )

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
        section_number=section_number,
        section_code=section_code,
        subsection_number=subsection_number,
        part_number=part_number,
        book_number=book_number,
        warnings=warnings,
    )


def build_volume_number(parsed):
    base = parsed.subsection_number or parsed.section_number
    pieces = [base]
    if parsed.part_number:
        pieces.append(parsed.part_number)
    if parsed.book_number:
        pieces.append(parsed.book_number)
    return ".".join(pieces)


def build_folder_number(parsed):
    if parsed.section_code == "ИОС":
        return build_volume_number(parsed)
    return parsed.part_number


def build_volume_code(parsed):
    pieces = [f"{PROJECT_CODE}-{parsed.section_code}"]
    for value in (parsed.subsection_number, parsed.part_number, parsed.book_number):
        if value:
            pieces.append(value)
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
    return ", ".join([value for value in values if value])


def validate_source_file(path):
    warnings = []
    if not path.exists():
        raise ValueError("файл не найден")
    if not path.is_file():
        raise ValueError("выбранный путь не является файлом")
    if not path.suffix:
        warnings.append("У файла нет расширения. Обработка продолжится, но проверьте имя файла в ИУЛ.")
    elif path.suffix.lower() != ".pdf":
        warnings.append(f"Файл не PDF ({path.suffix}). Обработка продолжится, потому что ИУЛ строится по имени и метаданным файла.")
    try:
        with open(path, "rb") as file:
            file.read(1)
    except OSError as exc:
        raise ValueError(f"файл заблокирован или недоступен для чтения: {exc}") from exc
    return warnings


def build_values(source_path, change_number="1", log=None):
    log = log or (lambda _text: None)
    path = Path(source_path)
    warnings = []
    log("      Проверяю существование файла, расширение и доступ на чтение")
    warnings.extend(validate_source_file(path))
    log("      Ищу шифр раздела, номера раздела/подраздела/части/книги в имени")
    parsed = parse_file_name(path)
    warnings.extend(parsed.warnings)
    log("      Читаю размер и дату последнего изменения файла")
    try:
        stat = path.stat()
    except OSError as exc:
        raise ValueError(f"не удалось получить метаданные файла: {exc}") from exc
    try:
        modified = datetime.fromtimestamp(stat.st_mtime)
    except (OSError, OverflowError, ValueError) as exc:
        modified = datetime.now()
        warnings.append(f"Не удалось определить дату изменения файла. Использована текущая дата: {exc}.")
    log("      Считаю CRC32")
    try:
        crc = crc32_file(path)
    except OSError as exc:
        raise ValueError(f"CRC не посчиталась: {exc}") from exc
    section_code = parsed.section_code

    log("      Подбираю ФИО, должность, наименования раздела/части/книги")
    people = {role: PEOPLE[role].get(section_code, "") for role in PEOPLE}
    main_person = "Левченко А.И.\n(ПИ-059768)"

    values = {
        "[Номер_раздела]": f"Раздел ПД №{parsed.section_number}",
        "[Номер_части]": f"Часть №{parsed.part_number}" if parsed.part_number else "",
        "[Книга]": f"Книга №{parsed.book_number}" if parsed.book_number else "",
        "[Шифр_раздела]": section_code,
        "[Номер_тома]": build_volume_number(parsed),
        "[Номер_подраздела]": f"Подраздел ПД №{parsed.subsection_number}" if parsed.subsection_number else "",
        "[Номер_раздела_2]": f"Раздел {parsed.section_number}",
        "[Наименование_раздела]": SECTION_NAMES.get(section_code, ""),
        "[Наименование_подраздела]": "Подраздел 1. Система электроснабжения" if section_code == "ИОС" else "",
        "[Номер_части_2]": f"Часть {parsed.part_number}" if parsed.part_number else "",
        "[Наименование_части]": PART_NAMES.get((section_code, parsed.part_number), "") if parsed.part_number else "",
        "[Номер_книги_2]": f"Книга {parsed.book_number}" if parsed.book_number else "",
        "[Наименование_книги]": BOOK_NAMES.get(parsed.book_number, "") if parsed.book_number else "",
        "[Шифр_тома]": build_volume_code(parsed),
        "[Номер_папки]": build_folder_number(parsed),
        "[Номер_изменения]": change_number,
        "[CRC_сумма]": crc,
        "[Наименование_файла]": path.name,
        "[Дата_последнего_изменения]": modified.strftime("%d.%m.%Y"),
        "[Время_последнего_изменения]": modified.strftime("%H:%M"),
        "[Размер_файла]": format_bytes(stat.st_size),
        "[Разработал]": people["Разработал"],
        "[Проверил]": people["Проверил"],
        "[Нормоконтролер]": people["Нормоконтролер"],
        "[Утвердил]": people["Утвердил"],
        "[Главный_проекта]": PROJECT_ROLE.get(section_code, ""),
        "[Главный_проекта_фамилия]": main_person,
        "[Наименование_файла_УЛ]": f"{path.name}_УЛ",
    }

    values["__row2__"] = build_row2(parsed)
    values["__people__"] = people
    log("      Словарь подстановок собран")
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
    for index in range(1, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise ValueError(f"не удалось подобрать свободное имя файла для {path.name}")


def find_signature(person_name):
    person_key = normalize_spaces(person_name).casefold()
    exact = []
    surname_matches = []
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
        names = ", ".join(path.name for path in surname_matches)
        return None, f"Для '{person_name}' найдено несколько подписей по фамилии: {names}."
    return None, ""


def fit_picture_to_cell(sheet, cell, image_path):
    shape = sheet.Shapes.AddPicture(str(image_path), False, True, cell.Left, cell.Top, -1, -1)
    shape.LockAspectRatio = True
    max_width = cell.Width * SIGNATURE_CELL_WIDTH_FACTOR
    max_height = cell.Height * SIGNATURE_CELL_HEIGHT_FACTOR
    warning = ""
    if max_width < MIN_SIGNATURE_CELL_WIDTH or max_height < MIN_SIGNATURE_CELL_HEIGHT:
        warning = f"Ячейка для подписи слишком маленькая: {cell.Address}."
    if shape.Width > max_width:
        shape.Width = max_width
    if shape.Height > max_height:
        shape.Height = max_height
    shape.Left = cell.Left + (cell.Width - shape.Width) / 2
    shape.Top = cell.Top + (cell.Height - shape.Height) / 2
    return warning


def replace_placeholders(workbook, values):
    warnings = []
    found_placeholders = set()
    for sheet in workbook.Worksheets:
        used = sheet.UsedRange
        for row in range(1, used.Rows.Count + 1):
            for col in range(1, used.Columns.Count + 1):
                cell = sheet.Cells(row, col)
                value = cell.Value2
                if not isinstance(value, str) or "[" not in value:
                    continue

                if "[Номер_папки]" in value and "[Номер_раздела]" in value and "[Шифр_раздела]" in value:
                    found_placeholders.update(re.findall(r"\[[^\]]+\]", value))
                    cell.Value = values["__row2__"]
                    continue

                original = value
                for placeholder, role in SIGNATURE_PLACEHOLDERS.items():
                    if placeholder in original:
                        found_placeholders.add(placeholder)
                        person = values["__people__"].get(role, "")
                        image_path, signature_lookup_warning = find_signature(person)
                        if signature_lookup_warning:
                            warnings.append(signature_lookup_warning)
                        cell.Value = original.replace(placeholder, "")
                        if image_path:
                            try:
                                signature_warning = fit_picture_to_cell(sheet, cell.MergeArea, image_path)
                                if signature_warning:
                                    warnings.append(signature_warning)
                            except Exception as exc:
                                warnings.append(f"Не удалось вставить подпись '{person}': {exc}.")
                        else:
                            warnings.append(f"Не найдена картинка подписи для '{person}'.")
                        original = cell.Value2 or ""

                for placeholder, replacement in values.items():
                    if not placeholder.startswith("["):
                        continue
                    if placeholder in original:
                        found_placeholders.add(placeholder)
                    original = str(original).replace(placeholder, str(replacement))

                cell.Value = clean_empty_lines(original)
                cell.WrapText = True

    if not found_placeholders:
        warnings.append("В шаблоне не найдено ни одного плейсхолдера для заполнения.")
    missing = sorted(CRITICAL_TEMPLATE_PLACEHOLDERS - found_placeholders)
    if missing:
        warnings.append("В шаблоне не найдены важные плейсхолдеры: " + ", ".join(missing) + ".")
    return warnings


def find_leftover_placeholders(workbook, known_placeholders):
    leftovers = []
    for sheet in workbook.Worksheets:
        used = sheet.UsedRange
        for row in range(1, used.Rows.Count + 1):
            for col in range(1, used.Columns.Count + 1):
                value = sheet.Cells(row, col).Value2
                if not isinstance(value, str):
                    continue
                remaining = [placeholder for placeholder in known_placeholders if placeholder in value]
                if remaining:
                    address = sheet.Cells(row, col).Address(False, False)
                    leftovers.append(f"{sheet.Name}!{address}: {', '.join(remaining)}")
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
        self.excel.EnableEvents = False
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
    log = log or (lambda _text: None)
    if session is None:
        with ExcelSession() as owned_session:
            return _export_one_inner(source_path, output_dir, change_number, owned_session, log, owns_session=True)
    return _export_one_inner(source_path, output_dir, change_number, session, log, owns_session=False)


def _export_one_inner(source_path, output_dir, change_number, session, log, owns_session=False):
    source_path = Path(source_path).resolve()
    output_dir = Path(output_dir).resolve()
    log("  1/12 Проверяю исходный файл и права чтения")
    if not TEMPLATE_PATH.exists():
        raise ValueError(f"не найден шаблон: {TEMPLATE_PATH}")
    if not SIGNATURES_DIR.exists():
        raise ValueError(f"не найдена папка с подписями: {SIGNATURES_DIR}")

    log("  2/12 Разбираю название файла")
    built = build_values(source_path, change_number, log=log)
    values = built.values
    all_warnings = list(built.warnings)
    for warning in built.warnings:
        log(f"      Предупреждение: {warning}")

    if not build_volume_number(built.parsed):
        raise ValueError("невозможно собрать корректный номер тома")
    volume_code = build_volume_code(built.parsed)
    if ".." in volume_code or volume_code.endswith("."):
        raise ValueError(f"шифр тома собран некорректно: {volume_code}")
    log(f"      Раздел: {built.parsed.section_code}, номер раздела: {built.parsed.section_number or '-'}, часть: {built.parsed.part_number or '-'}, книга: {built.parsed.book_number or '-'}")
    log(f"      Номер тома: {build_volume_number(built.parsed)}, шифр тома: {volume_code}")

    log("  3/12 Готовлю папки результата")
    editable_dir = output_dir / EDITABLE_DIR_NAME
    editable_dir.mkdir(parents=True, exist_ok=True)

    log("  4/12 Подбираю имена выходных файлов")
    base_name = safe_output_name(source_path)
    desired_xlsx = (editable_dir / f"{base_name}.xlsx").resolve()
    desired_pdf = (output_dir / f"{base_name}.pdf").resolve()
    xlsx_path = unique_path(desired_xlsx)
    pdf_path = unique_path(desired_pdf)
    if len(Path(source_path).stem) > MAX_OUTPUT_STEM:
        warning = "Длинное имя файла сокращено для совместимости с Excel/Windows."
        all_warnings.append(warning)
        log(f"      Предупреждение: {warning}")
    if xlsx_path != desired_xlsx:
        warning = f"Excel-файл уже существовал, выбрано новое имя: {xlsx_path.name}"
        all_warnings.append(warning)
        log(f"      Предупреждение: {warning}")
    if pdf_path != desired_pdf:
        warning = f"PDF-файл уже существовал, выбрано новое имя: {pdf_path.name}"
        all_warnings.append(warning)
        log(f"      Предупреждение: {warning}")
    log(f"      Excel: {xlsx_path.name}")
    log(f"      PDF: {pdf_path.name}")

    log("  5/12 Копирую шаблон Excel")
    shutil.copy2(TEMPLATE_PATH, xlsx_path)

    workbook = None
    try:
        if owns_session:
            log("  6/12 Запускаю Excel")
        else:
            log("  6/12 Использую уже открытый Excel для пакетной обработки")
        log("  7/12 Открываю копию шаблона")
        workbook = session.excel.Workbooks.Open(str(xlsx_path))
        log("  8/12 Заменяю текстовые переменные и вставляю подписи")
        warnings = replace_placeholders(workbook, values)
        all_warnings.extend(warnings)
        for warning in warnings:
            log(f"      Предупреждение: {warning}")
        log("  9/12 Проверяю, что плейсхолдеры не остались в книге")
        known_placeholders = {key for key in values if key.startswith("[")} | set(SIGNATURE_PLACEHOLDERS)
        leftovers = find_leftover_placeholders(workbook, known_placeholders)
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
            workbook = None


# ---------------------------------------------------------------------------
# Диалог настроек
# ---------------------------------------------------------------------------

class SettingsDialog:
    _ROLES = ["Разработал", "Проверил", "Нормоконтролер", "Утвердил"]
    _SECTIONS = ["АР", "КР", "ПЗУ", "ИОС"]

    def __init__(self, parent):
        top = Toplevel(parent)
        top.title("Настройки")
        top.resizable(False, False)
        top.grab_set()
        top.focus_set()
        self.top = top

        outer = ttk.Frame(top, padding=20)
        outer.pack(fill=BOTH, expand=True)

        # Шифр проекта
        code_frame = ttk.LabelFrame(outer, text="Проект", padding=10)
        code_frame.pack(fill=X, pady=(0, 12))
        ttk.Label(code_frame, text="Шифр проекта:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self._code_var = StringVar(value=PROJECT_CODE)
        ttk.Entry(code_frame, textvariable=self._code_var, width=22).grid(row=0, column=1, sticky="w")

        # Таблица ответственных лиц
        people_frame = ttk.LabelFrame(outer, text="Ответственные лица", padding=10)
        people_frame.pack(fill=X, pady=(0, 12))

        for col, section in enumerate(self._SECTIONS, start=1):
            ttk.Label(people_frame, text=section, font=("Segoe UI", 9, "bold"), anchor="center").grid(
                row=0, column=col, padx=6, pady=(0, 6), sticky="ew")

        self._vars: dict[str, dict[str, StringVar]] = {}
        for row_idx, role in enumerate(self._ROLES, start=1):
            lbl = "Нормоконтр.:" if role == "Нормоконтролер" else f"{role}:"
            ttk.Label(people_frame, text=lbl, anchor="w").grid(
                row=row_idx, column=0, sticky="w", padx=(0, 10), pady=4)
            self._vars[role] = {}
            for col, section in enumerate(self._SECTIONS, start=1):
                var = StringVar(value=PEOPLE.get(role, {}).get(section, ""))
                self._vars[role][section] = var
                ttk.Entry(people_frame, textvariable=var, width=17).grid(
                    row=row_idx, column=col, padx=6, pady=4)

        # Шаблон
        tmpl_frame = ttk.LabelFrame(outer, text="Шаблон", padding=10)
        tmpl_frame.pack(fill=X, pady=(0, 12))
        self._tmpl_label = ttk.Label(tmpl_frame, text=str(TEMPLATE_PATH), style="Muted.TLabel",
                                     wraplength=500, justify="left")
        self._tmpl_label.pack(anchor="w")
        ttk.Button(tmpl_frame, text="Заменить шаблон…", command=self._replace_template).pack(
            anchor="w", pady=(6, 0))

        # Кнопки
        btn_frame = ttk.Frame(outer)
        btn_frame.pack(fill=X, pady=(4, 0))
        ttk.Button(btn_frame, text="Отмена", command=top.destroy).pack(side=RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="Сохранить", command=self._save,
                   style="Accent.TButton").pack(side=RIGHT)

        # Центрируем диалог относительно родителя
        top.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        dw, dh = top.winfo_width(), top.winfo_height()
        top.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

    def _replace_template(self):
        path = filedialog.askopenfilename(
            title="Выберите новый шаблон",
            filetypes=[("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            shutil.copy2(path, TEMPLATE_PATH)
            self._tmpl_label.configure(text=str(TEMPLATE_PATH))
            messagebox.showinfo("Шаблон заменён", "Новый шаблон скопирован и будет использоваться при следующей генерации.", parent=self.top)
        except OSError as exc:
            messagebox.showerror("Ошибка", f"Не удалось скопировать шаблон:\n{exc}", parent=self.top)

    def _save(self):
        people = {}
        for role in self._ROLES:
            people[role] = {section: self._vars[role][section].get().strip()
                            for section in self._SECTIONS}

        config: dict = {}
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass

        config["project_code"] = self._code_var.get().strip()
        config["people"] = people

        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки:\n{exc}", parent=self.top)
            return

        load_config()
        self.top.destroy()
        messagebox.showinfo("Настройки", "Настройки сохранены и применены.")


# ---------------------------------------------------------------------------
# Главное окно
# ---------------------------------------------------------------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Создание ИУЛ")
        self.root.configure(bg="#f4f6f8")
        self.files = []
        self.output_var = StringVar()
        self.change_var = StringVar(value="1")
        self.log_file_path = None
        self.ui_queue = queue.Queue()
        self.worker_thread = None

        self.setup_style()

        shell = ttk.Frame(root, padding=16, style="App.TFrame")
        shell.pack(fill=BOTH, expand=True)

        # Заголовок
        header = ttk.Frame(shell, style="App.TFrame")
        header.pack(fill=X, pady=(0, 10))
        ttk.Label(header, text="Создание информационно-удостоверяющих листов",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Выберите исходные файлы, папку результата и запустите пакетную обработку.",
                  style="Muted.TLabel").pack(anchor="w", pady=(3, 0))

        # Панель действий
        actions = ttk.Frame(shell, style="Panel.TFrame", padding=10)
        actions.pack(fill=X, pady=(0, 8))
        ttk.Button(actions, text="Добавить файлы", command=self.add_files,
                   style="Accent.TButton").pack(side=LEFT)
        ttk.Button(actions, text="Очистить список", command=self.clear_files).pack(side=LEFT, padx=8)
        ttk.Button(actions, text="⚙ Настройки", command=self.show_settings).pack(side=RIGHT)
        ttk.Button(actions, text="Подписи ↗", command=self.open_signatures_dir).pack(side=RIGHT, padx=8)
        ttk.Button(actions, text="Открыть шаблон", command=self.open_template).pack(side=RIGHT)

        # Справка по имени файла
        hint_panel = ttk.LabelFrame(shell, text="Требования к имени файла", padding=(10, 6))
        hint_panel.pack(fill=X, pady=(0, 6))
        hint_text = (
            "Формат:   Раздел ПД №N  [подраздел ПД №N]  ШифрРаздела  [часть №N]  [книга №N].pdf\n"
            "Шифры:    АР  •  КР  •  ПЗУ  •  ИОС\n"
            "Примеры:  «Раздел ПД №3 АР часть №4.pdf»  •  «Раздел ПД №5 подраздел ПД №1 ИОС1 часть №1 книга №3.pdf»"
        )
        ttk.Label(hint_panel, text=hint_text, style="Muted.TLabel", justify="left").pack(anchor="w")

        # Таблица файлов
        files_panel = ttk.LabelFrame(shell, text="Файлы для обработки", padding=10)
        files_panel.pack(fill=BOTH, expand=True, pady=(0, 8))
        self.files_table = ttk.Treeview(
            files_panel,
            columns=("name", "status", "parsed", "folder"),
            show="headings",
            height=7,
        )
        self.files_table.heading("name", text="Файл")
        self.files_table.heading("status", text="")
        self.files_table.heading("parsed", text="Раздел / Часть / Книга")
        self.files_table.heading("folder", text="Папка")
        self.files_table.column("name", width=255, anchor="w")
        self.files_table.column("status", width=28, anchor="center", stretch=False)
        self.files_table.column("parsed", width=195, anchor="w")
        self.files_table.column("folder", width=340, anchor="w")
        self.files_table.tag_configure("ok", foreground="#16a34a")
        self.files_table.tag_configure("warn", foreground="#d97706")
        self.files_table.tag_configure("error", foreground="#dc2626")
        self.files_table.pack(fill=BOTH, expand=True)

        # Настройки запуска
        run_panel = ttk.Frame(shell, style="Panel.TFrame", padding=10)
        run_panel.pack(fill=X, pady=(0, 8))
        ttk.Label(run_panel, text="Папка результата").grid(row=0, column=0, sticky="w")
        ttk.Entry(run_panel, textvariable=self.output_var).grid(
            row=1, column=0, sticky="ew", pady=(4, 0), padx=(0, 8))
        ttk.Button(run_panel, text="Обзор", command=self.choose_output).grid(
            row=1, column=1, sticky="ew", pady=(4, 0))
        ttk.Label(run_panel, text="Номер изменения").grid(
            row=0, column=2, sticky="w", padx=(16, 0))
        ttk.Entry(run_panel, textvariable=self.change_var, width=8).grid(
            row=1, column=2, sticky="w", pady=(4, 0), padx=(16, 0))
        self.run_button = ttk.Button(run_panel, text="Создать ИУЛ", command=self.run,
                                     style="Accent.TButton")
        self.run_button.grid(row=1, column=3, sticky="e", pady=(4, 0), padx=(12, 0))
        run_panel.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(shell, mode="determinate")
        self.progress.pack(fill=X, pady=(0, 8))

        # Журнал
        log_panel = ttk.LabelFrame(shell, text="Журнал", padding=10)
        log_panel.pack(fill=BOTH, expand=True)
        self.log = Text(log_panel, height=7, wrap="word", bg="#ffffff", fg="#17202a",
                        relief="flat", padx=8, pady=8)
        log_scroll = ttk.Scrollbar(log_panel, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.configure(state=DISABLED)
        self.log.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll.pack(side=RIGHT, fill="y")

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("App.TFrame", background="#f4f6f8")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("Title.TLabel", background="#f4f6f8", foreground="#17202a",
                        font=("Segoe UI", 15, "bold"))
        style.configure("Muted.TLabel", background="#f4f6f8", foreground="#667085",
                        font=("Segoe UI", 9))
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9), padding=(12, 7))
        style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff",
                        padding=(14, 8))
        style.map("Accent.TButton",
                  background=[("active", "#1d4ed8"), ("disabled", "#93a4bd")])
        style.configure("Treeview", rowheight=25, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    # ------------------------------------------------------------------
    # Управление файлами
    # ------------------------------------------------------------------

    def _parse_for_display(self, file_path):
        try:
            parsed = parse_file_name(file_path)
            parts = [parsed.section_code]
            if parsed.section_number:
                parts.append(f"№{parsed.section_number}")
            if parsed.subsection_number:
                parts.append(f"Подр.{parsed.subsection_number}")
            if parsed.part_number:
                parts.append(f"Ч.{parsed.part_number}")
            if parsed.book_number:
                parts.append(f"Кн.{parsed.book_number}")
            summary = " | ".join(parts)
            if parsed.warnings:
                return "⚠", f"{summary}  ({len(parsed.warnings)} пред.)", "warn"
            return "✓", summary, "ok"
        except Exception as exc:
            short = str(exc)
            if len(short) > 55:
                short = short[:52] + "..."
            return "✗", short, "error"

    def add_files(self):
        files = filedialog.askopenfilenames(title="Выберите файлы для ИУЛ")
        if not files:
            return
        if len(self.files) + len(files) > MAX_FILES_PER_BATCH:
            messagebox.showwarning(
                "Слишком много файлов",
                f"За один запуск можно обработать не больше {MAX_FILES_PER_BATCH} файлов.",
            )
            files = files[: max(0, MAX_FILES_PER_BATCH - len(self.files))]
        for file in files:
            if file not in self.files:
                self.files.append(file)
                path = Path(file)
                symbol, summary, tag = self._parse_for_display(file)
                self.files_table.insert(
                    "", END,
                    values=(path.name, symbol, summary, str(path.parent)),
                    tags=(tag,),
                )
        if not self.output_var.get() and self.files:
            self.output_var.set(str(Path(self.files[0]).parent))

    def clear_files(self):
        self.files = []
        for item in self.files_table.get_children():
            self.files_table.delete(item)

    def choose_output(self):
        directory = filedialog.askdirectory(title="Куда сохранить ИУЛ")
        if directory:
            self.output_var.set(directory)

    # ------------------------------------------------------------------
    # Кнопки панели инструментов
    # ------------------------------------------------------------------

    def open_template(self):
        if not TEMPLATE_PATH.exists():
            messagebox.showerror("Ошибка", f"Шаблон не найден:\n{TEMPLATE_PATH}")
            return
        os.startfile(str(TEMPLATE_PATH))

    def open_signatures_dir(self):
        if not SIGNATURES_DIR.exists():
            try:
                SIGNATURES_DIR.mkdir(parents=True)
            except OSError as exc:
                messagebox.showerror("Ошибка", f"Не удалось создать папку подписей:\n{exc}")
                return
        os.startfile(str(SIGNATURES_DIR))

    def show_settings(self):
        SettingsDialog(self.root)

    # ------------------------------------------------------------------
    # Журнал
    # ------------------------------------------------------------------

    def write_log(self, text):
        self.log.configure(state=NORMAL)
        self.log.insert(END, text + "\n")
        self.log.see(END)
        self.log.configure(state=DISABLED)
        if self.log_file_path:
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(text + "\n")
            except OSError:
                pass
        self.root.update_idletasks()

    def clear_log(self):
        self.log.configure(state=NORMAL)
        self.log.delete("1.0", END)
        self.log.configure(state=DISABLED)

    # ------------------------------------------------------------------
    # Запуск обработки
    # ------------------------------------------------------------------

    def run(self):
        if not TEMPLATE_PATH.exists():
            messagebox.showerror("Ошибка", f"Не найден шаблон: {TEMPLATE_PATH}")
            return
        if not self.files:
            messagebox.showwarning("Нет файлов", "Добавьте один или несколько файлов.")
            return
        output_dir = self.output_var.get().strip()
        if not output_dir:
            messagebox.showwarning("Нет папки", "Выберите папку результата.")
            return
        if len(self.files) > MAX_FILES_PER_BATCH:
            messagebox.showwarning("Слишком много файлов",
                                   f"За один запуск можно обработать не больше {MAX_FILES_PER_BATCH} файлов.")
            return

        change_number = self.change_var.get().strip() or "1"
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Ошибка папки", f"Не удалось создать папку результата:\n{exc}")
            return
        self.clear_log()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = LOG_DIR / f"ИУЛ_журнал_{timestamp}.txt"
        self.write_log(f"Старт обработки: файлов {len(self.files)}, папка результата: {output_dir}")
        self.write_log(f"Файл журнала: {self.log_file_path}")
        self.run_button.configure(state=DISABLED)
        self.progress.configure(maximum=len(self.files), value=0)
        self.worker_thread = threading.Thread(
            target=self.run_worker,
            args=(list(self.files), output_dir, change_number),
            daemon=True,
        )
        self.worker_thread.start()
        self.root.after(100, self.process_ui_queue)

    def queue_log(self, text):
        self.ui_queue.put(("log", text))

    def run_worker(self, files, output_dir, change_number):
        ok = 0
        failed = 0
        warnings_count = 0
        try:
            self.queue_log("Запускаю Excel для пакетной обработки")
            with ExcelSession() as session:
                for index, file in enumerate(files, start=1):
                    try:
                        self.queue_log("")
                        self.queue_log(f"[{index}/{len(files)}] Файл: {Path(file).name}")
                        xlsx_path, pdf_path, warnings = export_one(
                            file,
                            output_dir,
                            change_number,
                            session=session,
                            log=self.queue_log,
                        )
                        ok += 1
                        warnings_count += len(warnings)
                        self.queue_log(f"  Готово: Excel сохранен: {xlsx_path}")
                        self.queue_log(f"  Готово: PDF сохранен: {pdf_path}")
                    except Exception as exc:
                        failed += 1
                        self.queue_log(f"  ОШИБКА: {exc}")
                        self.queue_log("  Файл пропущен, перехожу к следующему.")
                        self.queue_log("  Полный traceback:")
                        for line in traceback.format_exc().splitlines():
                            self.queue_log("    " + line)
                    self.ui_queue.put(("progress", index))
        finally:
            self.ui_queue.put(("done", ok, failed, warnings_count))

    def process_ui_queue(self):
        done_payload = None
        while True:
            try:
                item = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if item[0] == "log":
                self.write_log(item[1])
            elif item[0] == "progress":
                self.progress.configure(value=item[1])
            elif item[0] == "done":
                done_payload = item

        if done_payload:
            _kind, ok, failed, warnings_count = done_payload
            self.write_log("")
            self.write_log("Excel закрыт. Обработка завершена.")
            self.run_button.configure(state=NORMAL)
            messagebox.showinfo(
                "Готово",
                f"Создано: {ok}\nОшибок: {failed}\nПредупреждений: {warnings_count}\n\nЖурнал:\n{self.log_file_path}",
            )
            return

        if self.worker_thread and (self.worker_thread.is_alive() or not self.ui_queue.empty()):
            self.root.after(100, self.process_ui_queue)


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

def main():
    if not sys.platform.startswith("win"):
        raise RuntimeError("Программа рассчитана на Windows с установленным Microsoft Excel.")
    root = Tk()
    root.geometry("900x680")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
