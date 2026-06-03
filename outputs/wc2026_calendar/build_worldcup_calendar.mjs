import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.join(__dirname);
const outputPath = path.join(outputDir, "calendar_chm_2026_msk.xlsx");

const csv = `match_no,date,kickoff_local,stadium_tz,city,stadium,group,team_a,team_b
1,2026-06-11,13:00,America/Mexico_City,Mexico City,Estadio Azteca,A,Mexico,South Africa
2,2026-06-11,20:00,America/Mexico_City,Guadalajara,Estadio Akron,A,South Korea,Czechia
3,2026-06-12,15:00,America/Toronto,Toronto,BMO Field,B,Canada,Bosnia & Herzegovina
4,2026-06-12,18:00,America/Los_Angeles,Los Angeles,SoFi Stadium,D,USA,Paraguay
5,2026-06-13,12:00,America/Los_Angeles,San Francisco,Levi's Stadium,B,Qatar,Switzerland
6,2026-06-13,18:00,America/New_York,New Jersey,MetLife Stadium,C,Brazil,Morocco
7,2026-06-13,21:00,America/New_York,Boston,Gillette Stadium,C,Haiti,Scotland
8,2026-06-14,09:00,America/Vancouver,Vancouver,BC Place,D,Australia,Türkiye
9,2026-06-14,12:00,America/Chicago,Houston,NRG Stadium,E,Germany,Curaçao
10,2026-06-14,15:00,America/Chicago,Dallas,AT&T Stadium,F,Netherlands,Japan
11,2026-06-14,19:00,America/New_York,Philadelphia,Lincoln Financial Field,E,Ivory Coast,Ecuador
12,2026-06-14,20:00,America/Mexico_City,Monterrey,Estadio BBVA,F,Sweden,Tunisia
13,2026-06-15,12:00,America/New_York,Atlanta,Mercedes-Benz Stadium,H,Spain,Cape Verde
14,2026-06-15,12:00,America/Los_Angeles,Seattle,Lumen Field,G,Belgium,Egypt
15,2026-06-15,18:00,America/New_York,Miami,Hard Rock Stadium,H,Saudi Arabia,Uruguay
16,2026-06-15,18:00,America/Los_Angeles,Los Angeles,SoFi Stadium,G,Iran,New Zealand
17,2026-06-16,15:00,America/New_York,New Jersey,MetLife Stadium,I,France,Senegal
18,2026-06-16,18:00,America/New_York,Boston,Gillette Stadium,I,Iraq,Norway
19,2026-06-16,20:00,America/Chicago,Kansas City,Arrowhead Stadium,J,Argentina,Algeria
20,2026-06-16,21:00,America/Los_Angeles,San Francisco,Levi's Stadium,J,Austria,Jordan
21,2026-06-17,12:00,America/Chicago,Houston,NRG Stadium,K,Portugal,DR Congo
22,2026-06-17,15:00,America/Chicago,Dallas,AT&T Stadium,L,England,Croatia
23,2026-06-17,19:00,America/Toronto,Toronto,BMO Field,L,Ghana,Panama
24,2026-06-17,20:00,America/Mexico_City,Mexico City,Estadio Azteca,K,Uzbekistan,Colombia
25,2026-06-18,12:00,America/New_York,Atlanta,Mercedes-Benz Stadium,A,Czechia,South Africa
26,2026-06-18,12:00,America/Los_Angeles,Los Angeles,SoFi Stadium,B,Switzerland,Bosnia & Herzegovina
27,2026-06-18,15:00,America/Vancouver,Vancouver,BC Place,B,Canada,Qatar
28,2026-06-18,19:00,America/Mexico_City,Guadalajara,Estadio Akron,A,Mexico,South Korea
29,2026-06-19,12:00,America/Los_Angeles,Seattle,Lumen Field,D,USA,Australia
30,2026-06-19,18:00,America/New_York,Boston,Gillette Stadium,C,Scotland,Morocco
31,2026-06-19,20:30,America/New_York,Philadelphia,Lincoln Financial Field,C,Brazil,Haiti
32,2026-06-19,20:00,America/Los_Angeles,San Francisco,Levi's Stadium,D,Türkiye,Paraguay
33,2026-06-20,12:00,America/Chicago,Houston,NRG Stadium,F,Netherlands,Sweden
34,2026-06-20,16:00,America/Toronto,Toronto,BMO Field,E,Germany,Ivory Coast
35,2026-06-20,19:00,America/Chicago,Kansas City,Arrowhead Stadium,E,Ecuador,Curaçao
36,2026-06-20,22:00,America/Mexico_City,Monterrey,Estadio BBVA,F,Tunisia,Japan
37,2026-06-21,12:00,America/New_York,Atlanta,Mercedes-Benz Stadium,H,Spain,Saudi Arabia
38,2026-06-21,12:00,America/Los_Angeles,Los Angeles,SoFi Stadium,G,Belgium,Iran
39,2026-06-21,18:00,America/New_York,Miami,Hard Rock Stadium,H,Uruguay,Cape Verde
40,2026-06-21,18:00,America/Vancouver,Vancouver,BC Place,G,New Zealand,Egypt
41,2026-06-22,12:00,America/Chicago,Dallas,AT&T Stadium,J,Argentina,Austria
42,2026-06-22,17:00,America/New_York,Philadelphia,Lincoln Financial Field,I,France,Iraq
43,2026-06-22,20:00,America/New_York,New Jersey,MetLife Stadium,I,Norway,Senegal
44,2026-06-22,20:00,America/Los_Angeles,San Francisco,Levi's Stadium,J,Jordan,Algeria
45,2026-06-23,12:00,America/Chicago,Houston,NRG Stadium,K,Portugal,Uzbekistan
46,2026-06-23,16:00,America/New_York,Boston,Gillette Stadium,L,England,Ghana
47,2026-06-23,19:00,America/Toronto,Toronto,BMO Field,L,Panama,Croatia
48,2026-06-23,20:00,America/Mexico_City,Guadalajara,Estadio Akron,K,Colombia,DR Congo
49,2026-06-24,12:00,America/Vancouver,Vancouver,BC Place,B,Switzerland,Canada
50,2026-06-24,12:00,America/Los_Angeles,Seattle,Lumen Field,B,Bosnia & Herzegovina,Qatar
51,2026-06-24,18:00,America/New_York,Miami,Hard Rock Stadium,C,Scotland,Brazil
52,2026-06-24,18:00,America/New_York,Atlanta,Mercedes-Benz Stadium,C,Morocco,Haiti
53,2026-06-24,19:00,America/Mexico_City,Mexico City,Estadio Azteca,A,Czechia,Mexico
54,2026-06-24,19:00,America/Mexico_City,Monterrey,Estadio BBVA,A,South Africa,South Korea
55,2026-06-25,16:00,America/New_York,Philadelphia,Lincoln Financial Field,E,Curaçao,Ivory Coast
56,2026-06-25,16:00,America/New_York,New Jersey,MetLife Stadium,E,Ecuador,Germany
57,2026-06-25,18:00,America/Chicago,Dallas,AT&T Stadium,F,Japan,Sweden
58,2026-06-25,18:00,America/Chicago,Kansas City,Arrowhead Stadium,F,Tunisia,Netherlands
59,2026-06-25,19:00,America/Los_Angeles,Los Angeles,SoFi Stadium,D,Türkiye,USA
60,2026-06-25,19:00,America/Los_Angeles,San Francisco,Levi's Stadium,D,Paraguay,Australia
61,2026-06-26,15:00,America/New_York,Boston,Gillette Stadium,I,Norway,France
62,2026-06-26,15:00,America/Toronto,Toronto,BMO Field,I,Senegal,Iraq
63,2026-06-26,19:00,America/Chicago,Houston,NRG Stadium,H,Cape Verde,Saudi Arabia
64,2026-06-26,18:00,America/Mexico_City,Guadalajara,Estadio Akron,H,Uruguay,Spain
65,2026-06-26,20:00,America/Los_Angeles,Seattle,Lumen Field,G,Egypt,Iran
66,2026-06-26,20:00,America/Vancouver,Vancouver,BC Place,G,New Zealand,Belgium
67,2026-06-27,17:00,America/New_York,New Jersey,MetLife Stadium,L,Panama,England
68,2026-06-27,17:00,America/New_York,Philadelphia,Lincoln Financial Field,L,Croatia,Ghana
69,2026-06-27,19:30,America/New_York,Miami,Hard Rock Stadium,K,Colombia,Portugal
70,2026-06-27,19:30,America/New_York,Atlanta,Mercedes-Benz Stadium,K,DR Congo,Uzbekistan
71,2026-06-27,21:00,America/Chicago,Kansas City,Arrowhead Stadium,J,Algeria,Austria
72,2026-06-27,21:00,America/Chicago,Dallas,AT&T Stadium,J,Jordan,Argentina
73,2026-06-28,12:00,America/Los_Angeles,Los Angeles,SoFi Stadium,RO32,Runner-up A,Runner-up B
74,2026-06-29,12:00,America/Chicago,Houston,NRG Stadium,RO32,Winner C,Runner-up F
75,2026-06-29,16:30,America/New_York,Boston,Gillette Stadium,RO32,Winner E,Best 3rd (A/B/C/D/F)
76,2026-06-29,19:00,America/Mexico_City,Monterrey,Estadio BBVA,RO32,Winner F,Runner-up C
77,2026-06-30,12:00,America/Chicago,Dallas,AT&T Stadium,RO32,Runner-up E,Runner-up I
78,2026-06-30,17:00,America/New_York,New Jersey,MetLife Stadium,RO32,Winner I,Best 3rd (C/D/F/G/H)
79,2026-06-30,19:00,America/Mexico_City,Mexico City,Estadio Azteca,RO32,Winner A,Best 3rd (C/E/F/H/I)
80,2026-07-01,12:00,America/New_York,Atlanta,Mercedes-Benz Stadium,RO32,Winner L,Best 3rd (E/H/I/J/K)
81,2026-07-01,13:00,America/Los_Angeles,Seattle,Lumen Field,RO32,Winner G,Best 3rd (A/E/H/I/J)
82,2026-07-01,17:00,America/Los_Angeles,San Francisco,Levi's Stadium,RO32,Winner D,Best 3rd (B/E/F/I/J)
83,2026-07-02,12:00,America/Los_Angeles,Los Angeles,SoFi Stadium,RO32,Winner H,Runner-up J
84,2026-07-02,19:00,America/Toronto,Toronto,BMO Field,RO32,Runner-up K,Runner-up L
85,2026-07-02,20:00,America/Vancouver,Vancouver,BC Place,RO32,Winner B,Best 3rd (E/F/G/I/J)
86,2026-07-03,13:00,America/Chicago,Dallas,AT&T Stadium,RO32,Runner-up D,Runner-up G
87,2026-07-03,18:00,America/New_York,Miami,Hard Rock Stadium,RO32,Winner J,Runner-up H
88,2026-07-03,20:30,America/Chicago,Kansas City,Arrowhead Stadium,RO32,Winner K,Best 3rd (D/E/I/J/L)
90,2026-07-04,12:00,America/Chicago,Houston,NRG Stadium,RO16,W73,W75
89,2026-07-04,17:00,America/New_York,Philadelphia,Lincoln Financial Field,RO16,W74,W77
91,2026-07-05,16:00,America/New_York,New Jersey,MetLife Stadium,RO16,W76,W78
92,2026-07-05,18:00,America/Mexico_City,Mexico City,Estadio Azteca,RO16,W79,W80
93,2026-07-06,14:00,America/Chicago,Dallas,AT&T Stadium,RO16,W83,W84
94,2026-07-06,17:00,America/Los_Angeles,Seattle,Lumen Field,RO16,W81,W82
95,2026-07-07,12:00,America/New_York,Atlanta,Mercedes-Benz Stadium,RO16,W86,W88
96,2026-07-07,13:00,America/Vancouver,Vancouver,BC Place,RO16,W85,W87
97,2026-07-09,16:00,America/New_York,Boston,Gillette Stadium,QF,W89,W90
98,2026-07-10,12:00,America/Los_Angeles,Los Angeles,SoFi Stadium,QF,W93,W94
99,2026-07-11,17:00,America/New_York,Miami,Hard Rock Stadium,QF,W91,W92
100,2026-07-11,20:00,America/Chicago,Kansas City,Arrowhead Stadium,QF,W95,W96
101,2026-07-14,14:00,America/Chicago,Dallas,AT&T Stadium,SF,W97,W98
102,2026-07-15,15:00,America/New_York,Atlanta,Mercedes-Benz Stadium,SF,W99,W100
103,2026-07-18,17:00,America/New_York,Miami,Hard Rock Stadium,3RD,L101,L102
104,2026-07-19,15:00,America/New_York,New Jersey,MetLife Stadium,FIN,W101,W102`;

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(",");
  return lines.map((line) => {
    const values = [];
    let cur = "";
    let quoted = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') quoted = !quoted;
      else if (ch === "," && !quoted) {
        values.push(cur);
        cur = "";
      } else {
        cur += ch;
      }
    }
    values.push(cur);
    return Object.fromEntries(headers.map((h, i) => [h, values[i] ?? ""]));
  });
}

function zonedTimeToDate(dateStr, timeStr, tz) {
  const [y, mo, d] = dateStr.split("-").map(Number);
  const [h, mi] = timeStr.split(":").map(Number);
  const wantUtc = Date.UTC(y, mo - 1, d, h, mi);
  let guess = wantUtc;
  for (let iter = 0; iter < 4; iter++) {
    const parts = {};
    new Intl.DateTimeFormat("en-CA", {
      timeZone: tz,
      hour12: false,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).formatToParts(new Date(guess)).forEach((p) => {
      if (p.type !== "literal") parts[p.type] = Number(p.value);
    });
    const asWallUtc = Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour === 24 ? 0 : parts.hour, parts.minute);
    const diff = wantUtc - asWallUtc;
    if (diff === 0) break;
    guess += diff;
  }
  return new Date(guess);
}

function formatInTz(date, tz, opts) {
  return new Intl.DateTimeFormat("ru-RU", { timeZone: tz, ...opts }).format(date);
}

function excelDateFromDateOnly(date) {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
}

function stageLabel(group) {
  return ({
    RO32: "1/16 финала",
    RO16: "1/8 финала",
    QF: "Четвертьфинал",
    SF: "Полуфинал",
    "3RD": "Матч за 3 место",
    FIN: "Финал",
  })[group] || `Группа ${group}`;
}

function stageSort(group) {
  const order = ["A","B","C","D","E","F","G","H","I","J","K","L","RO32","RO16","QF","SF","3RD","FIN"];
  return order.indexOf(group);
}

const matches = parseCsv(csv).map((m) => {
  const kickoffUtc = zonedTimeToDate(m.date, m.kickoff_local, m.stadium_tz);
  const mskDateText = formatInTz(kickoffUtc, "Europe/Moscow", { year: "numeric", month: "2-digit", day: "2-digit" });
  const mskTimeText = formatInTz(kickoffUtc, "Europe/Moscow", { hour: "2-digit", minute: "2-digit", hour12: false });
  const mskIsoDate = mskDateText.split(".").reverse().join("-");
  const mskDate = excelDateFromDateOnly(new Date(`${mskIsoDate}T00:00:00Z`));
  const localDate = new Date(`${m.date}T00:00:00Z`);
  return {
    ...m,
    match_no: Number(m.match_no),
    stage: stageLabel(m.group),
    match: `${m.team_a} - ${m.team_b}`,
    kickoffUtc,
    utcText: kickoffUtc.toISOString().slice(0, 16).replace("T", " "),
    mskDate,
    mskTime: mskTimeText,
    mskDateTimeSort: `${mskIsoDate} ${mskTimeText}`,
    localDate,
    localDateText: m.date,
    localDateTime: `${m.date} ${m.kickoff_local}`,
  };
}).sort((a, b) => a.kickoffUtc - b.kickoffUtc || a.match_no - b.match_no);

const wb = Workbook.create();
const sheets = ["Календарь МСК", "Мой выбор", "Все матчи", "Группы", "Стадионы", "Источник"].map((name) => wb.worksheets.add(name));
const [cal, pick, all, groups, venues, source] = sheets;
for (const sheet of sheets) sheet.showGridLines = false;

const colors = {
  navy: "#12355B",
  blue: "#2F6F9F",
  teal: "#2A9D8F",
  gold: "#E9C46A",
  coral: "#E76F51",
  soft: "#F7F4EA",
  paleBlue: "#EAF3F8",
  paleGreen: "#EAF7F3",
  paleGold: "#FFF4D8",
  text: "#1F2933",
  muted: "#667085",
  border: "#D9E2EC",
  white: "#FFFFFF",
};

function title(sheet, range, text, subtitle) {
  sheet.mergeCells(range);
  const r = sheet.getRange(range);
  r.values = [[text]];
  r.format.fill.color = colors.navy;
  r.format.font.color = colors.white;
  r.format.font.bold = true;
  r.format.font.size = 18;
  r.format.horizontalAlignment = "center";
  r.format.verticalAlignment = "middle";
  r.format.rowHeightPx = 42;
  if (subtitle) {
    const cell = sheet.getCell(1, 0);
    cell.values = [[subtitle]];
    cell.format.font.color = colors.muted;
    cell.format.font.italic = true;
  }
}

function styleHeader(range) {
  range.format.fill.color = colors.blue;
  range.format.font.color = colors.white;
  range.format.font.bold = true;
  range.format.horizontalAlignment = "center";
  range.format.verticalAlignment = "middle";
  range.format.wrapText = true;
  range.format.borders = { preset: "all", style: "thin", color: colors.border };
}

function styleBody(range) {
  range.format.fill.color = colors.white;
  range.format.font.color = colors.text;
  range.format.borders = { preset: "all", style: "thin", color: colors.border };
  range.format.verticalAlignment = "middle";
}

function setWidths(sheet, widths) {
  widths.forEach((w, i) => {
    sheet.getCell(0, i).format.columnWidthPx = w;
  });
}

title(cal, "A1:K1", "Календарь матчей ЧМ-2026: время по Москве", "Отмечай матчи в колонке A: выбранные автоматически появятся на листе «Мой выбор».");
cal.getRange("A3:K3").values = [["Всего матчей", matches.length, "Групповой этап", 72, "Плей-офф", 32, "Первый матч", matches[0].mskDate, "Финал", matches.at(-1).mskDate, "MSK UTC+3"]];
cal.getRange("A3:K3").format.fill.color = colors.paleBlue;
cal.getRange("A3:K3").format.font.bold = true;
cal.getRange("H3:H3").setNumberFormat("dd.mm.yyyy");
cal.getRange("J3:J3").setNumberFormat("dd.mm.yyyy");

const calHeaders = ["Хочу смотреть", "Приоритет", "Дата МСК", "Время МСК", "Матч", "Стадия", "#", "Стадион", "Город", "Локальное время", "Заметки"];
const calRows = matches.map((m) => ["", "", m.mskDate, m.mskTime, m.match, m.stage, m.match_no, m.stadium, m.city, m.localDateTime, ""]);
cal.getRange("A5:K5").values = [calHeaders];
cal.getRangeByIndexes(5, 0, calRows.length, calHeaders.length).values = calRows;
styleHeader(cal.getRange("A5:K5"));
styleBody(cal.getRangeByIndexes(5, 0, calRows.length, calHeaders.length));
cal.getRange(`C6:C${5 + calRows.length}`).setNumberFormat("dd.mm.yyyy");
cal.getRange(`D6:D${5 + calRows.length}`).setNumberFormat("@");
cal.getRange(`G6:G${5 + calRows.length}`).setNumberFormat("0");
cal.getRange(`A6:A${5 + calRows.length}`).dataValidation = { rule: { type: "list", values: ["Да", "Нет"] } };
cal.getRange(`B6:B${5 + calRows.length}`).dataValidation = { rule: { type: "list", values: ["1", "2", "3", "4", "5"] } };
cal.getRange(`A6:K${5 + calRows.length}`).conditionalFormats.addCustom('=$A6="Да"', { fill: { color: colors.paleGreen }, font: { bold: true } });
cal.getRange(`F6:F${5 + calRows.length}`).conditionalFormats.add("containsText", { text: "Финал", format: { fill: { color: colors.paleGold }, font: { bold: true } } });
cal.freezePanes.freezeRows(5);
cal.tables.add(`A5:K${5 + calRows.length}`, true, "CalendarMSK");
setWidths(cal, [92, 82, 92, 82, 260, 120, 52, 190, 120, 150, 190]);

title(pick, "A1:K1", "Мой список матчей", "Сюда подтягиваются строки, где на листе «Календарь МСК» в колонке A стоит «Да».");
pick.getRange("A4:K4").values = [calHeaders];
styleHeader(pick.getRange("A4:K4"));
pick.getRange("A5").formulas = [[`=FILTER('Календарь МСК'!A6:K109,'Календарь МСК'!A6:A109="Да","Пока ничего не отмечено")`]];
pick.freezePanes.freezeRows(4);
setWidths(pick, [92, 82, 92, 82, 260, 120, 52, 190, 120, 150, 190]);

title(all, "A1:L1", "Полное расписание и исходные времена", "Есть время стадиона, UTC и пересчет в московское время.");
const allHeaders = ["#", "Дата МСК", "Время МСК", "UTC", "Дата/время стадиона", "Часовой пояс стадиона", "Матч", "Стадия", "Группа", "Стадион", "Город", "Источник"];
const allRows = matches.map((m) => [m.match_no, m.mskDate, m.mskTime, m.utcText, m.localDateTime, m.stadium_tz, m.match, m.stage, m.group, m.stadium, m.city, "kickofftimes.tv"]);
all.getRange("A4:L4").values = [allHeaders];
all.getRangeByIndexes(4, 0, allRows.length, allHeaders.length).values = allRows;
styleHeader(all.getRange("A4:L4"));
styleBody(all.getRangeByIndexes(4, 0, allRows.length, allHeaders.length));
all.getRange(`B5:B${4 + allRows.length}`).setNumberFormat("dd.mm.yyyy");
all.tables.add(`A4:L${4 + allRows.length}`, true, "AllMatches");
all.freezePanes.freezeRows(4);
setWidths(all, [52, 92, 82, 128, 140, 170, 260, 120, 70, 190, 120, 120]);

title(groups, "A1:F1", "Группы и стадии", "Сводка по количеству матчей.");
const groupSummary = Array.from(matches.reduce((map, m) => {
  const key = m.group;
  const cur = map.get(key) || { group: key, stage: m.stage, count: 0, first: m.mskDate, last: m.mskDate };
  cur.count += 1;
  cur.last = m.mskDate;
  map.set(key, cur);
  return map;
}, new Map()).values()).sort((a, b) => stageSort(a.group) - stageSort(b.group));
const groupRows = groupSummary.map((g) => [g.group, g.stage, g.count, g.first, g.last, g.group.length === 1 ? "Группа" : "Плей-офф"]);
groups.getRange("A4:F4").values = [["Код", "Стадия", "Матчей", "Первый матч МСК", "Последний матч МСК", "Тип"]];
groups.getRangeByIndexes(4, 0, groupRows.length, 6).values = groupRows;
styleHeader(groups.getRange("A4:F4"));
styleBody(groups.getRangeByIndexes(4, 0, groupRows.length, 6));
groups.getRange(`D5:E${4 + groupRows.length}`).setNumberFormat("dd.mm.yyyy");
groups.tables.add(`A4:F${4 + groupRows.length}`, true, "GroupsSummary");
const groupsChart = groups.charts.add("bar", groups.getRange(`A4:C${4 + groupRows.length}`));
groupsChart.title = "Матчи по группам и стадиям";
groupsChart.hasLegend = false;
groupsChart.xAxis = { axisType: "textAxis" };
groupsChart.yAxis = { numberFormatCode: "0" };
groupsChart.setPosition("H4", "N22");
setWidths(groups, [70, 150, 80, 130, 140, 100]);

title(venues, "A1:E1", "Стадионы", "Где сколько матчей проходит.");
const venueSummary = Array.from(matches.reduce((map, m) => {
  const key = `${m.stadium}|${m.city}`;
  const cur = map.get(key) || { stadium: m.stadium, city: m.city, count: 0, first: m.mskDate, last: m.mskDate };
  cur.count += 1;
  cur.last = m.mskDate;
  map.set(key, cur);
  return map;
}, new Map()).values()).sort((a, b) => b.count - a.count || a.city.localeCompare(b.city));
const venueRows = venueSummary.map((v) => [v.stadium, v.city, v.count, v.first, v.last]);
venues.getRange("A4:E4").values = [["Стадион", "Город", "Матчей", "Первый матч МСК", "Последний матч МСК"]];
venues.getRangeByIndexes(4, 0, venueRows.length, 5).values = venueRows;
styleHeader(venues.getRange("A4:E4"));
styleBody(venues.getRangeByIndexes(4, 0, venueRows.length, 5));
venues.getRange(`D5:E${4 + venueRows.length}`).setNumberFormat("dd.mm.yyyy");
venues.tables.add(`A4:E${4 + venueRows.length}`, true, "VenuesSummary");
setWidths(venues, [220, 130, 82, 130, 140]);

title(source, "A1:D1", "Источник и примечания", "");
source.getRange("A3:D8").values = [
  ["Что", "Значение", "", ""],
  ["Основной источник", "https://kickofftimes.tv/", "", ""],
  ["Официальная сверка", "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums", "", ""],
  ["Важно", "Kickoff Times указывает, что это независимое фанатское расписание, не связанное с FIFA.", "", ""],
  ["Часовой пояс файла", "Europe/Moscow / МСК UTC+3", "", ""],
  ["Дата сборки", new Date().toISOString().slice(0, 10), "", ""],
];
styleHeader(source.getRange("A3:D3"));
styleBody(source.getRange("A4:D8"));
setWidths(source, [150, 620, 20, 20]);

for (const sheet of sheets) {
  const used = sheet.getUsedRange();
  if (used) {
    used.format.font.name = "Aptos";
    used.format.wrapText = false;
  }
}

await fs.mkdir(outputDir, { recursive: true });

const check = await wb.inspect({
  kind: "table",
  range: "Календарь МСК!A1:K14",
  include: "values,formulas",
  tableMaxRows: 14,
  tableMaxCols: 11,
});
console.log(check.ndjson);

const errors = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

await wb.render({ sheetName: "Календарь МСК", range: "A1:K24", scale: 1.3 });
await wb.render({ sheetName: "Мой выбор", range: "A1:K14", scale: 1.3 });
await wb.render({ sheetName: "Группы", range: "A1:F23", scale: 1.3 });
await wb.render({ sheetName: "Стадионы", range: "A1:E22", scale: 1.3 });
await wb.render({ sheetName: "Источник", range: "A1:D9", scale: 1.3 });

const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(outputPath);
console.log(`Saved ${outputPath}`);
