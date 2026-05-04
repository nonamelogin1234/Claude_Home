using Autodesk.Revit.UI;
using Newtonsoft.Json.Linq;
using RevitMCPSDK.API.Base;
using RevitMCPSDK.API.Models.Results;
using RuRevitCommandSet.Models;
using RuRevitCommandSet.Services;

namespace RuRevitCommandSet.Commands
{
    // Команда "create_grid_ru" — регистрируется в command.json
    // Получает пролёты осей и создаёт сетку по ГОСТ
    public class CreateGridRuCommand : ExternalEventCommandBase
    {
        // Ссылка на наш обработчик для удобного доступа к Parameters и Result
        private readonly CreateGridRuHandler _handler;

        // Плагин передаёт UIApplication при загрузке командсета
        public CreateGridRuCommand(UIApplication uiApp)
            : base(new CreateGridRuHandler(), uiApp)
        {
            // Handler — публичное свойство базового класса, хранит наш обработчик
            _handler = (CreateGridRuHandler)Handler;
        }

        // Имя должно точно совпадать с "commandName" в command.json
        public override string CommandName => "create_grid_ru";

        // Точка входа от MCP — parameters это JSON с полями vertical_spans и horizontal_spans
        public override object Execute(JObject parameters, string requestId)
        {
            var request = parameters.ToObject<CreateGridRuRequest>();

            if (request?.VerticalSpans == null || request.VerticalSpans.Count == 0)
                return new CommandResult { Success = false, ErrorMessage = "vertical_spans не указаны" };

            if (request?.HorizontalSpans == null || request.HorizontalSpans.Count == 0)
                return new CommandResult { Success = false, ErrorMessage = "horizontal_spans не указаны" };

            // Передаём параметры и запускаем обработчик в главном потоке Revit
            _handler.Parameters = request;
            bool completed = RaiseAndWaitForCompletion(30000);

            if (!completed)
                return new CommandResult { Success = false, ErrorMessage = "Таймаут: Revit не ответил за 30 секунд" };

            return _handler.Result;
        }
    }
}
