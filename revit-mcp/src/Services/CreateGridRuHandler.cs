using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using RevitMCPSDK.API.Interfaces;
using RevitMCPSDK.API.Models.Results;
using RuRevitCommandSet.Models;

namespace RuRevitCommandSet.Services
{
    // Обработчик выполняется в главном потоке Revit через механизм ExternalEvent
    public class CreateGridRuHandler : IExternalEventHandler, IWaitableExternalEventHandler
    {
        // Синхронизация: команда ждёт, пока обработчик не закончит работу
        private readonly ManualResetEvent _resetEvent = new ManualResetEvent(false);

        // Параметры, которые команда передаёт перед запуском
        public CreateGridRuRequest Parameters { get; set; }

        // Результат, который команда читает после завершения
        public CommandResult Result { get; private set; }

        // Буквы осей по ГОСТ 21.101 — пропущены Ё, З, Й, О, Ъ, Ы, Ь
        private static readonly char[] GostLetters = "АБВГДЕЖИКЛМНПРСТУФХЦЧШЩЭЮЯ".ToCharArray();

        // Revit вызывает этот метод в своём главном потоке
        public void Execute(UIApplication app)
        {
            // Сбрасываем событие перед работой — иначе повторный вызов сразу вернёт старый результат
            _resetEvent.Reset();

            try
            {
                var doc = app.ActiveUIDocument.Document;
                var req = Parameters;
                var letterAxes = new List<string>();
                var numberAxes = new List<string>();

                // vertical_spans — пролёты между вертикальными (цифровыми) осями → ширина сетки
                // horizontal_spans — пролёты между горизонтальными (буквенными) осями → высота сетки
                double totalWidth = req.VerticalSpans.Sum();
                double totalHeight = req.HorizontalSpans.Sum();

                // Оси выходят за крайние пролёты на 1500 мм с каждой стороны
                double margin = ToFeet(1500);
                double xMin = -margin;
                double xMax = ToFeet(totalWidth) + margin;
                double yMin = -margin;
                double yMax = ToFeet(totalHeight) + margin;

                using (var tx = new Transaction(doc, "Создать оси"))
                {
                    tx.Start();

                    // Вертикальные линии → цифровые оси 1, 2, 3... (parallel to Y)
                    double x = 0;
                    for (int i = 0; i <= req.VerticalSpans.Count; i++)
                    {
                        string name = (i + 1).ToString();
                        var line = Line.CreateBound(new XYZ(x, yMin, 0), new XYZ(x, yMax, 0));
                        var grid = Grid.Create(doc, line);
                        grid.Name = name;
                        numberAxes.Add(name);

                        if (i < req.VerticalSpans.Count)
                            x += ToFeet(req.VerticalSpans[i]);
                    }

                    // Горизонтальные линии → буквенные оси А, Б, В... (parallel to X)
                    double y = 0;
                    for (int i = 0; i <= req.HorizontalSpans.Count; i++)
                    {
                        string name = GetGostLetter(i);
                        var line = Line.CreateBound(new XYZ(xMin, y, 0), new XYZ(xMax, y, 0));
                        var grid = Grid.Create(doc, line);
                        grid.Name = name;
                        letterAxes.Add(name);

                        if (i < req.HorizontalSpans.Count)
                            y += ToFeet(req.HorizontalSpans[i]);
                    }

                    tx.Commit();
                }

                Result = new CommandResult
                {
                    Success = true,
                    Data = new CreateGridRuResult
                    {
                        LetterAxes = letterAxes,
                        NumberAxes = numberAxes,
                        TotalWidthMm = totalWidth,
                        TotalHeightMm = totalHeight
                    }
                };
            }
            catch (Exception ex)
            {
                Result = new CommandResult
                {
                    Success = false,
                    ErrorMessage = ex.Message
                };
            }
            finally
            {
                // Сигнализируем команде, что работа завершена
                _resetEvent.Set();
            }
        }

        public string GetName() => "CreateGridRuHandler";

        // Команда ждёт здесь, пока Execute не вызовет _resetEvent.Set()
        public bool WaitForCompletion(int timeoutMs) => _resetEvent.WaitOne(timeoutMs);

        // Миллиметры → футы (внутренние единицы Revit)
        private static double ToFeet(double mm) => mm / 304.8;

        // Буква оси по порядковому номеру (0→А, 1→Б, ..., 25→Я, 26→АА, ...)
        private static string GetGostLetter(int index)
        {
            if (index < GostLetters.Length)
                return GostLetters[index].ToString();

            int outer = index / GostLetters.Length - 1;
            int inner = index % GostLetters.Length;
            return GostLetters[outer].ToString() + GostLetters[inner].ToString();
        }
    }
}
