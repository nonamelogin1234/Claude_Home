# -*- coding: utf-8 -*-
"""Труба в одну линию — дублирует штатный инструмент Revit (вкладка Системы)."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit

cmd_id = RevitCommandId.LookupCommandId("ID_PIPE_1LINE_PATH")
revit.uiapp.PostCommand(cmd_id)
