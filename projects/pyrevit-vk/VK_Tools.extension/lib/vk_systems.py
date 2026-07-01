# -*- coding: utf-8 -*-
"""Общая логика скрытия/показа инженерных систем ВК по имени типа системы
(ADSK_Водопровод_В1, ADSK_Канализация_К1 и т.п.). Используется кнопками-
переключателями на панели Видимость.
"""

from pyrevit import revit, DB, script

MEP_CATEGORIES = [
    DB.BuiltInCategory.OST_PipeCurves,
    DB.BuiltInCategory.OST_PipeFitting,
    DB.BuiltInCategory.OST_PipeAccessory,
    DB.BuiltInCategory.OST_PipeInsulations,
    DB.BuiltInCategory.OST_FlexPipeCurves,
]


def get_hideable_views(doc):
    """Виды, на которых имеет смысл скрывать/показывать элементы."""
    skip_types = (DB.ViewSchedule, DB.ViewSheet, DB.ViewDrafting)
    views = []
    for v in DB.FilteredElementCollector(doc).OfClass(DB.View):
        if v.IsTemplate:
            continue
        if isinstance(v, skip_types):
            continue
        if not v.CanBePrinted:
            continue
        views.append(v)
    return views


def get_system_type_ids(doc, type_name):
    """ElementId типов PipingSystemType с точным именем (например,
    'ADSK_Водопровод_В1')."""
    ids = []
    for st in DB.FilteredElementCollector(doc).OfClass(DB.Plumbing.PipingSystemType):
        if st.Name == type_name:
            ids.append(st.Id)
    return ids


def get_element_ids_for_type_ids(doc, type_ids):
    """MEP-элементы (трубы, фитинги, арматура, изоляция), у которых параметр
    'Тип системы' (RBS_SYSTEM_TYPE_PARAM) ссылается на один из type_ids."""
    type_id_set = set(t.IntegerValue for t in type_ids)
    if not type_id_set:
        return []

    cat_filters = [DB.ElementCategoryFilter(c) for c in MEP_CATEGORIES]
    multi_cat_filter = DB.LogicalOrFilter(cat_filters)
    collector = (
        DB.FilteredElementCollector(doc)
        .WherePasses(multi_cat_filter)
        .WhereElementIsNotElementType()
    )

    matched = []
    for el in collector:
        p = el.get_Parameter(DB.BuiltInParameter.RBS_SYSTEM_TYPE_PARAM)
        if p is None:
            continue
        type_id = p.AsElementId()
        if type_id and type_id.IntegerValue in type_id_set:
            matched.append(el.Id)
    return matched


def is_hidden_in_view(view, elem_ids):
    """Считаем систему скрытой, если скрыт хотя бы один её элемент в активном
    виде (нет смысла требовать 100% совпадения — так надёжнее для щитовых
    видов, где часть элементов может быть недоступна)."""
    for eid in elem_ids:
        el = view.Document.GetElement(eid)
        if el is not None and el.IsHidden(view):
            return True
    return False


def toggle_system(type_name, abbr):
    """Скрывает систему во всех видах, если она сейчас видна, и наоборот.
    Возвращает True, если после операции система скрыта, False если показана,
    None если система с таким именем типа не найдена в проекте."""
    doc = revit.doc
    logger = script.get_logger()

    type_ids = get_system_type_ids(doc, type_name)
    elem_ids = get_element_ids_for_type_ids(doc, type_ids)

    if not elem_ids:
        logger.warning(
            "Система '%s' (тип '%s') не найдена в проекте — "
            "проверьте, что в проекте есть система с таким именем типа.",
            abbr, type_name,
        )
        return None

    active_view = revit.active_view
    should_hide = not is_hidden_in_view(active_view, elem_ids)

    id_list = DB.List[DB.ElementId](elem_ids)
    views = get_hideable_views(doc)

    with revit.Transaction("VK: {} {}".format("Скрыть" if should_hide else "Показать", abbr)):
        for v in views:
            try:
                if should_hide:
                    v.HideElements(id_list)
                else:
                    v.UnhideElements(id_list)
            except Exception:
                # вид может не поддерживать скрытие для этой категории —
                # пропускаем, не прерывая обработку остальных видов
                pass

    return should_hide
