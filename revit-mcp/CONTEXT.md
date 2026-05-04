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
- Сборка: `dotnet build -c "Debug R24"` → DLL автоматом копируется в папку Addins
- Кириллица в именах осей: буквы по ГОСТ (без Ё, З, Й, О, Ъ, Ы, Ь)

## Готовые команды

| Команда | Статус | Описание |
|---------|--------|----------|
| `create_grid_custom` | 🔧 в разработке | Сетка осей с произвольными пролётами |

## Параметры create_grid_custom

```json
{
  "vertical_spans": [5680, 7050],    // пролёты между осями А,Б,В (мм)
  "horizontal_spans": [750, 7330, 2660]  // пролёты между осями 1,2,3,4 (мм)
}
```

Результат: вертикальные А=0, Б=5680, В=12730 + горизонтальные 1=0, 2=750, 3=8080, 4=10740.
