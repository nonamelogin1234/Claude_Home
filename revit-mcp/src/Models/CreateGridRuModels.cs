using Newtonsoft.Json;
using System.Collections.Generic;

namespace RuRevitCommandSet.Models
{
    // Входные параметры команды create_grid_ru
    public class CreateGridRuRequest
    {
        // Пролёты между буквенными осями А→Б, Б→В... в мм
        // Пример: [5680, 7050] создаёт оси А, Б, В
        [JsonProperty("vertical_spans")]
        public List<double> VerticalSpans { get; set; }

        // Пролёты между цифровыми осями 1→2, 2→3... в мм
        // Пример: [750, 7330, 2660] создаёт оси 1, 2, 3, 4
        [JsonProperty("horizontal_spans")]
        public List<double> HorizontalSpans { get; set; }
    }

    // Результат — что было создано
    public class CreateGridRuResult
    {
        // Имена созданных буквенных осей (А, Б, В...)
        [JsonProperty("letter_axes")]
        public List<string> LetterAxes { get; set; }

        // Имена созданных цифровых осей (1, 2, 3...)
        [JsonProperty("number_axes")]
        public List<string> NumberAxes { get; set; }

        // Итоговые размеры сетки в мм
        [JsonProperty("total_width_mm")]
        public double TotalWidthMm { get; set; }

        [JsonProperty("total_height_mm")]
        public double TotalHeightMm { get; set; }
    }
}
