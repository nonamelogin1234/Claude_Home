# Паттерн новой команды — методичка

## Структура (3 файла на команду)

```
src/
├── Commands/XxxCommand.cs     — точка входа от MCP
├── Services/XxxHandler.cs     — работа с Revit API
└── Models/XxxModels.cs        — Request/Result классы
```

## 1. Models/XxxModels.cs

```csharp
using Newtonsoft.Json;
using System.Collections.Generic;

namespace RuRevitCommandSet.Models
{
    public class XxxRequest
    {
        [JsonProperty("param_name")]
        public ТипДанных ParamName { get; set; }
        // ... другие параметры
    }

    public class XxxResult
    {
        [JsonProperty("created_ids")]
        public List<long> CreatedIds { get; set; }
        // ... что вернуть пользователю
    }
}
```

## 2. Services/XxxHandler.cs

```csharp
using System;
using System.Threading;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using RevitMCPSDK.API.Interfaces;
using RevitMCPSDK.API.Models.Results;
using RuRevitCommandSet.Models;

namespace RuRevitCommandSet.Services
{
    public class XxxHandler : IExternalEventHandler, IWaitableExternalEventHandler
    {
        private readonly ManualResetEvent _resetEvent = new ManualResetEvent(false);
        public XxxRequest Parameters { get; set; }
        public CommandResult Result { get; private set; }

        public void Execute(UIApplication app)
        {
            _resetEvent.Reset(); // ОБЯЗАТЕЛЬНО — сброс перед работой

            try
            {
                var doc = app.ActiveUIDocument.Document;

                // --- ВСЯ РАБОТА С REVIT API ЗДЕСЬ ---
                // Единицы: всё в ФУТАХ! mm / 304.8

                using (var tx = new Transaction(doc, "Описание транзакции"))
                {
                    tx.Start();
                    // ... создаём элементы ...
                    tx.Commit();
                }

                Result = new CommandResult { Success = true, Data = new XxxResult { ... } };
            }
            catch (Exception ex)
            {
                Result = new CommandResult { Success = false, ErrorMessage = ex.Message };
            }
            finally
            {
                _resetEvent.Set(); // ОБЯЗАТЕЛЬНО — всегда в finally
            }
        }

        public string GetName() => "XxxHandler";
        public bool WaitForCompletion(int timeoutMs) => _resetEvent.WaitOne(timeoutMs);

        // Конвертация мм → футы
        private static double ToFeet(double mm) => mm / 304.8;
    }
}
```

## 3. Commands/XxxCommand.cs

```csharp
using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPSDK.API.Base;
using RevitMCPSDK.API.Models.Results;
using RuRevitCommandSet.Models;
using RuRevitCommandSet.Services;

namespace RuRevitCommandSet.Commands
{
    public class XxxCommand : ExternalEventCommandBase
    {
        private readonly XxxHandler _handler;

        public XxxCommand(UIApplication uiApp) : base(new XxxHandler(), uiApp)
        {
            _handler = (XxxHandler)Handler;
        }

        public override string CommandName => "xxx_command_name"; // совпадает с command.json

        public override object Execute(JObject parameters, string requestId)
        {
            var request = parameters.ToObject<XxxRequest>();

            // Валидация входных данных
            if (request == null)
                return new CommandResult { Success = false, ErrorMessage = "Нет параметров" };

            _handler.Parameters = request;
            bool completed = RaiseAndWaitForCompletion(30000);

            if (!completed)
                return new CommandResult { Success = false, ErrorMessage = "Таймаут 30 сек" };

            return _handler.Result;
        }
    }
}
```

## 4. Регистрация

### В command.json (наш манифест):
```json
{
  "commandName": "xxx_command_name",
  "description": "Описание команды",
  "assemblyPath": "RuRevitCommandSet.dll"
}
```

### В commandRegistry.json (реестр плагина):
```json
{
  "commandName": "xxx_command_name",
  "assemblyPath": "RuRevitCommandSet\\{VERSION}\\RuRevitCommandSet.dll",
  "enabled": true,
  "supportedRevitVersions": ["2024"],
  "developer": { "name": "Sergei", "organization": "RuRevitMCP" },
  "description": "Описание команды"
}
```

## 5. Сборка и деплой

```bash
# Сборка — DLL автоматом копируется в папку Revit
"C:\Program Files\dotnet\dotnet.exe" build src\RuRevitCommandSet.csproj

# Нужен рестарт Revit после добавления НОВОЙ команды
# При изменении существующей — можно перегружать через send_code_to_revit или через hot-reload плагина
```

## Ключевые грабли

- `_resetEvent.Reset()` — в НАЧАЛЕ Execute(), иначе повторные вызовы сломаются
- Всегда `_resetEvent.Set()` в `finally` — иначе команда зависнет
- Единицы Revit — ФУТЫ. `mm / 304.8`
- `send_code_to_revit` НЕ открывает внешнюю транзакцию — можно создавать `Transaction` внутри
  (но в нашем Handler транзакция нужна, т.к. он выполняется через ExternalEvent)
- Кириллица в именах элементов (оси ГОСТ) работает нормально

## Тестирование логики без компиляции

Перед написанием Handler — протестировать логику через `send_code_to_revit`:
```csharp
// Никаких Transaction не нужно — send_code_to_revit сам управляет
var line = Line.CreateBound(new XYZ(0,0,0), new XYZ(5,0,0));
var wall = Wall.Create(document, line, level.Id, false);
return "OK: " + wall.Id;
```
