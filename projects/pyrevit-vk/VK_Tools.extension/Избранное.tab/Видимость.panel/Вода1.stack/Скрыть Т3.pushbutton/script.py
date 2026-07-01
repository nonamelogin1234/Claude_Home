# -*- coding: utf-8 -*-
"""Скрыть/показать систему Т3 (ADSK_Водопровод_Т3, ГВС подача) во всех видах.
Клик — переключатель, без диалогов: галочка в тексте кнопки = система скрыта."""
from pyrevit import script
import vk_systems

TYPE_NAME = "ADSK_Водопровод_Т3"
ABBR = "Т3"


def _label(hidden):
    return (u"☑ " if hidden else u"☐ ") + ABBR


def __selfinit__(script_cmp, ui_button_cmp, __rvt__):
    try:
        state = vk_systems.get_current_state(TYPE_NAME)
        ui_button_cmp.set_title(_label(bool(state)))
    except Exception:
        pass
    return True


script.get_output().close()

hidden = vk_systems.toggle_system(TYPE_NAME, ABBR)
if hidden is not None:
    script.get_button().set_title(_label(hidden))
