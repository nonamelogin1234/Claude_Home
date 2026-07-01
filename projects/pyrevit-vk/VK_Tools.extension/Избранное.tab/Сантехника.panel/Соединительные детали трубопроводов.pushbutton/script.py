# -*- coding: utf-8 -*-
"""Соединительные детали трубопроводов — дублирует штатный инструмент Revit
(вкладка Системы)."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit

cmd_id = RevitCommandId.LookupCommandId("ID_RBS_PIPE_FITTING")
revit.uiapp.PostCommand(cmd_id)
