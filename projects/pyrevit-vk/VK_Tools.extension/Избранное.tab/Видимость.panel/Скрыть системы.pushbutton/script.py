# -*- coding: utf-8 -*-
"""Скрыть/показать инженерные системы (В1, В2, К1, К2 и т.д.) во всём проекте.

Собирает все типы систем трубопроводов и воздуховодов, найденные в проекте,
показывает список с чекбоксами. Отмеченные системы будут скрыты во всех
видах проекта, неотмеченные — показаны (Unhide) во всех видах, где были
скрыты ранее этим же инструментом.
"""

from pyrevit import revit, DB, forms, script

doc = revit.doc
logger = script.get_logger()
output = script.get_output()

MEP_CATEGORIES = [
    DB.BuiltInCategory.OST_PipeCurves,
    DB.BuiltInCategory.OST_PipeFitting,
    DB.BuiltInCategory.OST_PipeAccessory,
    DB.BuiltInCategory.OST_PipeInsulations,
    DB.BuiltInCategory.OST_DuctCurves,
    DB.BuiltInCategory.OST_DuctFitting,
    DB.BuiltInCategory.OST_DuctAccessory,
    DB.BuiltInCategory.OST_DuctTerminal,
    DB.BuiltInCategory.OST_FlexPipeCurves,
    DB.BuiltInCategory.OST_FlexDuctCurves,
]

SYSTEM_TYPE_CLASSES = [DB.Plumbing.PipingSystemType, DB.Mechanical.DuctSystemType]


def get_system_types_by_abbreviation():
    """Возвращает {аббревиатура: [ElementId типа системы, ...]}."""
    result = {}
    for cls in SYSTEM_TYPE_CLASSES:
        collector = DB.FilteredElementCollector(doc).OfClass(cls)
        for system_type in collector:
            abbr_param = system_type.get_Parameter(
                DB.BuiltInParameter.RBS_SYSTEM_ABBREVIATION_PARAM
            )
            abbr = abbr_param.AsString() if abbr_param else None
            if not abbr:
                continue
            result.setdefault(abbr, []).append(system_type.Id)
    return result


def get_element_ids_for_type_ids(type_ids):
    """Находит все MEP-элементы, у которых параметр 'Тип системы'
    ссылается на один из указанных типов систем."""
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


def get_hideable_views():
    """Виды, в которых вообще имеет смысл скрывать/показывать элементы
    (не шаблоны, не листы, не спецификации/легенды)."""
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


def main():
    system_types = get_system_types_by_abbreviation()
    if not system_types:
        forms.alert(
            "В проекте не найдено ни одной системы трубопроводов/воздуховодов "
            "с заполненной аббревиатурой (В1, К1 и т.п.).",
            exitscript=True,
        )

    abbreviations = sorted(system_types.keys())

    selected = forms.SelectFromList.show(
        abbreviations,
        title="Скрыть системы (отметьте, что нужно СКРЫТЬ)",
        button_name="Применить",
        multiselect=True,
    )

    if selected is None:
        script.exit()

    selected_set = set(selected)
    views = get_hideable_views()
    if not views:
        forms.alert("В проекте нет видов, на которых можно скрывать элементы.", exitscript=True)

    hidden_count = 0
    shown_count = 0
    errors = []

    with revit.Transaction("VK: Скрыть/показать инженерные системы"):
        for abbr in abbreviations:
            elem_ids = get_element_ids_for_type_ids(system_types[abbr])
            if not elem_ids:
                continue

            should_hide = abbr in selected_set
            id_list = DB.List[DB.ElementId](elem_ids)

            for v in views:
                try:
                    if should_hide:
                        v.HideElements(id_list)
                        hidden_count += 1
                    else:
                        v.UnhideElements(id_list)
                        shown_count += 1
                except Exception as ex:
                    # часть видов может не поддерживать скрытие конкретных
                    # категорий (например, 3D-вид с выключенной категорией) —
                    # пропускаем такие виды, не прерывая обработку остальных
                    errors.append("{} / {}: {}".format(abbr, v.Name, ex))

    output.print_md("### Готово")
    output.print_md("Скрыто операций: **{}**, показано операций: **{}**".format(
        hidden_count, shown_count
    ))
    if errors:
        output.print_md("Пропущено (вид не поддерживает скрытие для этой категории): {}".format(
            len(errors)
        ))
        logger.debug("\n".join(errors))


if __name__ == "__main__":
    main()
