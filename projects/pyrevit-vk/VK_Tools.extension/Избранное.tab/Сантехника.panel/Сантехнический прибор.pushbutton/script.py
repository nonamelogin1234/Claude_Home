# -*- coding: utf-8 -*-
"""Сантехнический прибор — дублирует штатный инструмент Revit (вкладка
Системы)."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit

cmd_id = RevitCommandId.LookupCommandId("ID_RBS_PLUMBING_FIXTURE")
revit.uiapp.PostCommand(cmd_id)
