# -*- coding: utf-8 -*-
"""Труба — дублирует штатный инструмент Revit (вкладка Системы -> Сантехника
и трубопроводы -> Труба). Запускает ту же самую команду Revit."""
from Autodesk.Revit.UI import RevitCommandId
from pyrevit import revit, script

script.get_output().close()

cmd_id = RevitCommandId.LookupCommandId("ID_RBS_PIPE_PIPE")
revit.uiapp.PostCommand(cmd_id)
