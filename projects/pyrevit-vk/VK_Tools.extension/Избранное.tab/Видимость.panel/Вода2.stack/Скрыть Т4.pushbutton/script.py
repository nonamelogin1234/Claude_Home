# -*- coding: utf-8 -*-
"""Скрыть/показать систему Т4 (ADSK_Водопровод_Т4, ГВС циркуляция) во всех видах.
Клик — переключатель: скрыто -> показать, показано -> скрыть.
"""
from pyrevit import script, revit
import vk_systems

TYPE_NAME = "ADSK_Водопровод_Т4"
ABBR = "Т4"


def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
    try:
        doc = revit.doc
        type_ids = vk_systems.get_system_type_ids(doc, TYPE_NAME)
        elem_ids = vk_systems.get_element_ids_for_type_ids(doc, type_ids)
        hidden = bool(elem_ids) and vk_systems.is_hidden_in_view(revit.active_view, elem_ids)
        script.toggle_icon(hidden)
    except Exception:
        script.toggle_icon(False)
    return True


hidden = vk_systems.toggle_system(TYPE_NAME, ABBR)
if hidden is not None:
    script.toggle_icon(hidden)
