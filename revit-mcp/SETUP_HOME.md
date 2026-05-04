# Инструкция: первый запуск на домашнем ПК

## Что нужно сделать один раз

### 1. Установить .NET SDK (если нет)
Скачать с https://dotnet.microsoft.com/download → .NET SDK (последняя версия)

### 2. Убедиться что mcp-servers-for-revit установлен
Папка должна существовать:
```
%APPDATA%\Autodesk\Revit\Addins\2024\revit_mcp_plugin\
```
Если нет — установить плагин (как на рабочем ПК).

### 3. Склонировать репо (если ещё не)
```
git clone https://github.com/nonamelogin1234/Claude_Home.git
```
Или просто `git pull` если уже есть.

### 4. Запустить деплой
```powershell
cd путь\до\Claude_Home\revit-mcp
powershell -ExecutionPolicy Bypass -File deploy.ps1
```
Скрипт сам:
- Соберёт DLL
- Добавит команду в commandRegistry.json
- Скажет "перезапусти Revit"

### 5. Перезапустить Revit

### 6. Проверить
В Claude Desktop попросить: `create_grid_ru с vertical_spans [3000] и horizontal_spans [4000]`

---

## Дальше (каждая сессия)

```
git pull   ← получить новые команды
```

Если добавлялись НОВЫЕ команды → снова `deploy.ps1` + перезапуск Revit.
Если правили существующие → только `deploy.ps1` (без перезапуска, hot-reload работает).

---

## Что где лежит

| Что | Где |
|-----|-----|
| Исходники C# | `revit-mcp/src/` (в гите) |
| Скомпилированная DLL | `%APPDATA%\Autodesk\Revit\Addins\2024\revit_mcp_plugin\Commands\RuRevitCommandSet\2024\` |
| Реестр команд | `%APPDATA%\Autodesk\Revit\Addins\2024\revit_mcp_plugin\commandRegistry.json` |
| Методичка по командам | `revit-mcp/COMMAND_PATTERN.md` |
