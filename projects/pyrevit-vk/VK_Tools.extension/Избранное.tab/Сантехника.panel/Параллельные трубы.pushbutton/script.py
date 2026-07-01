# -*- coding: utf-8 -*-
"""Параллельные трубы — дублирует штатный инструмент Revit (вкладка Системы)."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit

cmd_id = RevitCommandId.LookupCommandId("ID_PARALLEL_PIPES")
revit.uiapp.PostCommand(cmd_id)
