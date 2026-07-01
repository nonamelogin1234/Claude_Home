# -*- coding: utf-8 -*-
"""Гибкий трубопровод — дублирует штатный инструмент Revit (вкладка Системы)."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit

cmd_id = RevitCommandId.LookupCommandId("ID_RBS_PIPE_FLEX")
revit.uiapp.PostCommand(cmd_id)
