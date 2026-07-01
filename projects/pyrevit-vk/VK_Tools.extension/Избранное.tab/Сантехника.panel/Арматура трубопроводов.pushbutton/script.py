# -*- coding: utf-8 -*-
"""Арматура трубопроводов — дублирует штатный инструмент Revit (вкладка
Системы)."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit

cmd_id = RevitCommandId.LookupCommandId("ID_RBS_PIPE_ACCESSORY")
revit.uiapp.PostCommand(cmd_id)
