# ГРАБЛИ — REVIT MCP ПРОЕКТ

## SDK и архитектура

- Конструктор базового класса: `ExternalEventCommandBase(IWaitableExternalEventHandler handler, UIApplication uiApp)`
- Команда получает `UIApplication uiApp` в конструкторе — плагин передаёт его при инициализации
- `Handler` (публичное свойство базового класса) — наш обработчик после вызова `base(...)`
- Возвращаемый тип `Execute` — `object`, сериализуется в JSON. Используем `CommandResult` из SDK
- `AIResult<T>` — внутренний тип RevitMCPCommandSet, в нашем проекте не использовать. Только `CommandResult`

## ManualResetEvent

- После `Set()` событие остаётся установленным → при повторном вызове команды нужно сбросить
- Сбрасывать `_resetEvent.Reset()` в начале `Execute()` обработчика, ДО основной работы

## Регистрация команд

- `commandRegistry.json` — мастер-реестр плагина, нужно добавить нашу команду с путём `RuRevitCommandSet\{VERSION}\RuRevitCommandSet.dll`
- `command.json` в папке командсета — манифест для MCP сервера (JS сторона)
- assemblyPath в command.json — только имя DLL без пути: `"RuRevitCommandSet.dll"`
- assemblyPath в commandRegistry.json — путь с `{VERSION}`: `"RuRevitCommandSet\\{VERSION}\\RuRevitCommandSet.dll"`

## Сборка и деплой

- Целевая платформа: `net48` (Revit 2024 на .NET Framework 4.8)
- OutputPath в .csproj: `C:\Users\gor-r\AppData\Roaming\Autodesk\Revit\Addins\2024\revit_mcp_plugin\Commands\RuRevitCommandSet\2024\`
- `AppendTargetFrameworkToOutputPath` = false — иначе создаст подпапку net48/
- `Private = false` для RevitAPI.dll и RevitMCPSDK.dll — не копировать их в output (они уже есть в Revit)
- После сборки нужен рестарт Revit — плагин грузит DLL при старте

## Revit API — единицы

- Все размеры внутри Revit в ФУТАХ. Конвертация: `mm / 304.8`
- XYZ координаты — футы. Никогда не передавать миллиметры напрямую

## Оси по ГОСТ

- Буквы осей ГОСТ 21.101: А Б В Г Д Е Ж И К Л М Н П Р С Т У Ф Х Ц Ч Ш Щ Э Ю Я
- Пропускаем: Ё З Й О Ъ Ы Ь
- Буквенные оси (А,Б,В) = горизонтальные линии на плане (Line по оси X)
- Цифровые оси (1,2,3) = вертикальные линии на плане (Line по оси Y)

## Регистрация новых команд в MCP

- `commandRegistry.json` генерируется плагином автоматически при старте Revit из `command.json` каждого командсета
- Редактировать надо `Commands\RuRevitCommandSet\command.json` (задеплоенный), а НЕ `commandRegistry.json` напрямую
- `command.json` из src/ при сборке **не копировался** → добавлен post-build таргет в .csproj (с 2026-05-05)
- Порядок деплоя новой команды: 1) добавить в src/command.json, 2) собрать (command.json скопируется автоматически), 3) перезапустить Revit, 4) перезапустить Claude Code
- **ПРАВИЛЬНЫЙ способ добавить кастомный MCP-инструмент:** создать `.js` файл в `C:\Users\gor-r\AppData\Roaming\npm\node_modules\mcp-server-for-revit\build\tools\` с функцией `registerXxxTool(server)`. Файл подхватывается автоматически при следующем старте Claude Code — Revit перезапускать НЕ нужно.
- Паттерн файла: импорт z и withRevitConnection, экспорт registerXxxTool, внутри server.tool("name", "desc", {schema}, handler) где handler вызывает revitClient.sendCommand("name", args)

## "Method not found" при вызове команды

- Класс есть в DLL, commandRegistry.json правильный — но команда не вызывается
- Причина: `RevitCommandRegistry._commands` и `ExternalEventManager._events` — два отдельных словаря. Команда должна попасть в ОБА при старте Revit.
- Диагностика: через `send_code_to_revit` вывести ключи `_events` словаря ExternalEventManager — если команды нет, она не была зарегистрирована при загрузке плагина
- Подозрение на timing: если команда добавлена в command.json/DLL, но Revit читал реестр до обновления файлов — команда пропущена
- Лечение (гипотеза): полный перезапуск Revit с актуальным DLL и command.json, затем проверить _events

## PowerShell / рефлексия

- RevitAPI.dll и RevitAPIUI.dll нельзя загрузить через рефлексию без запущенного Revit — зависимости не резолвятся
- Для изучения SDK использовать `send_code_to_revit` — выполняется прямо внутри Revit
- AppDomain.CurrentDomain.GetAssemblies() внутри Revit даёт полный список загруженных сборок

## Объём материала в составных стенах (PartUtils)

- `GetMaterialVolume()` и `HOST_AREA_COMPUTED × fraction` — официально признанный баг Autodesk на угловых стыках. Дают завышенный результат.
- **Правильный метод: `PartUtils.CreateParts()`** — разбивает стену на слои с реальной геометрией стыков. Подтверждено: тестовые 4 стены [кирпич|штукатурка|бетон250|штукатурка] = 3.7600 м³ ✓
- `PartUtils.IsValidForCreateParts(document, id)` и `PartUtils.CreateParts(document, ids)` принимают **`LinkElementId`**, не `ElementId`. Конвертировать: `new LinkElementId(elementId)`
- `HOST_VOLUME_COMPUTED` на элементе Part возвращает 0 — объём брать через **геометрию солида**: `part.get_Geometry(opts)` → `Solid.Volume`
- Материал части: `part.get_Parameter(BuiltInParameter.DPART_MATERIAL_ID_PARAM).AsElementId()`
- `send_code_to_revit` уже обёрнут в транзакцию SDK → `new Transaction()` внутри падает с "not permitted". Использовать **`SubTransaction`** — работает корректно и откатывается через `st.RollBack()`
- Паттерн (рабочий):
  ```csharp
  var linkIds = wallIds.Select(id => new LinkElementId(id)).ToList();
  var st = new SubTransaction(document);
  st.Start();
  PartUtils.CreateParts(document, linkIds);
  document.Regenerate();
  // ... читать Part элементы, считать объём через геометрию ...
  st.RollBack();
  ```
