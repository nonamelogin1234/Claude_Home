# -*- coding: utf-8 -*-
"""Спринклер — дублирует штатный инструмент Revit (вкладка Системы)."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit

cmd_id = RevitCommandId.LookupCommandId("ID_RBS_SPRINKLER")
revit.uiapp.PostCommand(cmd_id)
