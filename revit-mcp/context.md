# RuRevitMCP — контекст проекта

## Что это

Пользовательский CommandSet для Revit MCP. Команды на C# (.NET 4.8, Revit 2024),
которые Claude вызывает через MCP протокол для автоматизации Revit.

## Архитектура

Использует `mcp-servers-for-revit` (npm пакет) как MCP сервер + плагин в Revit.
Пользовательский CommandSet подключается через `command.json`.

Паттерн каждой команды:
```
Commands/XxxCommand.cs         — ExternalEventCommandBase, точка входа от MCP
Services/XxxEventHandler.cs    — IExternalEventHandler + ManualResetEvent, выполняет Revit API
Models/XxxModels.cs            — Request/Result модели с JsonProperty
```

## Ключевые детали

- Все размеры **снаружи в мм**, внутри конвертируем `mm / 304.8` → футы (внутренние единицы Revit)
- `command.json` — регистрация команд, `assemblyPath`: просто `"RuRevitCommandSet.dll"`
- Сборка: `"C:\Program Files\dotnet\dotnet.exe" build src\RuRevitCommandSet.csproj` → DLL автоматом копируется в папку Addins
- Кириллица в именах осей: буквы по ГОСТ (без Ё, З, Й, О, Ъ, Ы, Ь)

## Статус

🟡 `create_wall_ru` — DLL собрана, класс загружен в Revit, commandRegistry.json правильный, но при вызове возвращает **"Method not found"**. Баг не воспроизводится на `create_grid_ru` и `get_model_state_ru`.

## Что сделано

- [2026-05-04] Создана структура проекта: src/ с .csproj, Models/, Commands/, Services/
- [2026-05-04] Написана команда `create_grid_ru` — создаёт сетку осей с произвольными пролётами
- [2026-05-04] Настроена сборка dotnet → DLL копируется в Addins автоматически
- [2026-05-04] commandRegistry.json обновлён — команда зарегистрирована
- [2026-05-04] Логика осей исправлена: vertical_spans → вертикальные линии (цифровые 1,2,3), horizontal_spans → горизонтальные линии (буквенные А,Б,В)
- [2026-05-04] Изучили что дают стандартные read-команды MCP (get_current_view_elements, analyze_model_statistics) — дают данные но в ФУТАХ
- [2026-05-04] Написан `get_model_state_ru` — читает модель компактно в мм (уровни, оси, стены). Работает.
- [2026-05-04] Написан `create_wall_ru` — создаёт стены по координатам в мм с поиском типа и уровня по частичному имени
- [2026-05-05] DLL собрана с тремя командами, commandRegistry.json содержит все три. Рефлексия подтвердила загрузку классов. Но `create_wall_ru` даёт "Method not found".
- [2026-05-05] Изучены внутренности RevitMCPPlugin через send_code_to_revit: `RevitCommandRegistry._commands: Dictionary`, `ExternalEventManager._events: Dictionary<String, ExternalEventWrapper>`. Подозрение — `create_wall_ru` не попал в один из этих словарей.

## Следующий шаг

**Починить "Method not found" для `create_wall_ru`.**

Следующий диагностический шаг (уже понятен — нужно выполнить):
```csharp
// Через send_code_to_revit — смотрим что в _events ExternalEventManager
var pluginAssembly = AppDomain.CurrentDomain.GetAssemblies().First(a => a.GetName().Name == "RevitMCPPlugin");
var eemType = pluginAssembly.GetType("revit_mcp_plugin.Core.ExternalEventManager");
var eem = eemType.GetField("_instance", BindingFlags.Static|BindingFlags.NonPublic).GetValue(null);
var events = (System.Collections.IDictionary)eemType.GetField("_events", BindingFlags.Instance|BindingFlags.NonPublic).GetValue(eem);
// Вывести events.Keys — есть ли там create_wall_ru?
```

Если `create_wall_ru` нет в `_events` — команда не зарегистрирована при инициализации плагина. Причина может быть: `LoadCommandFromAssembly` вызывался до того как DLL обновилась, или есть баг в timing загрузки.

## Параметры create_grid_ru

```json
{
  "vertical_spans": [5680, 7050],        // пролёты между вертикальными осями 1,2,3 (мм)
  "horizontal_spans": [750, 7330, 2660]  // пролёты между горизонтальными осями А,Б,В,Г (мм)
}
```

- `vertical_spans` → оси параллельны Y (вертикальные линии) → цифровые: 1=0, 2=5680, 3=12730
- `horizontal_spans` → оси параллельны X (горизонтальные линии) → буквенные: А=0, Б=750, В=8080, Г=10740

## Грабли

→ см. grabli_revit.md (отдельный файл)
