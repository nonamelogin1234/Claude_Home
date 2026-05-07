/* global React */
// Data + helpers for the IUL prototype.

const SAMPLE_FILES = [
  {
    id: 'f1',
    name: 'Раздел ПД №3 АР часть №4.pdf',
    section: 'АР',
    sectionLabel: 'Раздел 3 · Часть 4',
    sectionTone: 'tag-ar',
    size: '4.2 МБ',
    crc: 'A7F3 9E2C',
    date: '2026-04-28',
    status: 'idle',
    progress: 0,
    warnings: 0,
  },
  {
    id: 'f2',
    name: 'Раздел ПД №5 подраздел ПД №1 ИОС1 часть №1 книга №3.pdf',
    section: 'ИОС',
    sectionLabel: 'Раздел 5.1 · Книга 3',
    sectionTone: 'tag-ios',
    size: '12.8 МБ',
    crc: '3D81 04AB',
    date: '2026-04-28',
    status: 'idle',
    progress: 0,
    warnings: 0,
  },
  {
    id: 'f3',
    name: 'Раздел ПД №2 КР часть №1.pdf',
    section: 'КР',
    sectionLabel: 'Раздел 2 · Часть 1',
    sectionTone: 'tag-kr',
    size: '7.6 МБ',
    crc: 'B22C 17F0',
    date: '2026-04-27',
    status: 'idle',
    progress: 0,
    warnings: 0,
  },
  {
    id: 'f4',
    name: 'Раздел ПД №6 ПЗУ часть №2.pdf',
    section: 'ПЗУ',
    sectionLabel: 'Раздел 6 · Часть 2',
    sectionTone: 'tag-pzu',
    size: '2.1 МБ',
    crc: '9E45 8B12',
    date: '2026-04-27',
    status: 'idle',
    progress: 0,
    warnings: 0,
  },
  {
    id: 'f5',
    name: 'Раздел ПД №3 АР часть №2 книга №1.pdf',
    section: 'АР',
    sectionLabel: 'Раздел 3 · Часть 2 · Книга 1',
    sectionTone: 'tag-ar',
    size: '5.3 МБ',
    crc: 'C7AA 30F9',
    date: '2026-04-27',
    status: 'idle',
    progress: 0,
    warnings: 0,
  },
  {
    id: 'f6',
    name: 'Раздел ПД №5 подраздел ПД №2 ИОС2 часть №1.pdf',
    section: 'ИОС',
    sectionLabel: 'Раздел 5.2 · Часть 1',
    sectionTone: 'tag-ios',
    size: '8.9 МБ',
    crc: '2F60 1A4D',
    date: '2026-04-26',
    status: 'idle',
    progress: 0,
    warnings: 0,
  },
];

const PERSONS = [
  { role: 'Разработал', AR: 'Соколова М.В.', KR: 'Иванов В.И.', PZU: 'Соколова М.В.', IOS: 'Барахович Ю.В.' },
  { role: 'Проверил', AR: 'Герасимчук Е.И.', KR: 'Герасимчук Е.И.', PZU: 'Герасимчук Е.И.', IOS: 'Иванов В.И.' },
  { role: 'Нормоконтр.', AR: 'Матинов С.А.', KR: 'Матинов С.А.', PZU: 'Матинов С.А.', IOS: 'Матинов С.А.' },
  { role: 'Утвердил', AR: 'Левченко А.И.', KR: 'Левченко А.И.', PZU: 'Левченко А.И.', IOS: 'Левченко А.И.' },
];

const SIGNATURES = [
  { id: 's1', name: 'Соколова М.В.', role: 'Разработал · АР, ПЗУ', detected: true },
  { id: 's2', name: 'Иванов В.И.', role: 'Разработал · КР', detected: true },
  { id: 's3', name: 'Барахович Ю.В.', role: 'Разработал · ИОС', detected: true },
  { id: 's4', name: 'Герасимчук Е.И.', role: 'Проверил', detected: true },
  { id: 's5', name: 'Матинов С.А.', role: 'Нормоконтроль', detected: true },
  { id: 's6', name: 'Левченко А.И.', role: 'Утвердил', detected: false },
];

// Pre-canned sample log lines used by the console panel.
const SAMPLE_LOG = [
  { time: '14:02:11', level: 'info', msg: 'Запуск пакетной обработки · 6 файлов' },
  { time: '14:02:11', level: 'info', msg: 'Шаблон загружен: ИУЛ_шаблон.xlsx' },
  { time: '14:02:12', level: 'info', msg: 'Раздел ПД №3 АР часть №4.pdf · парсинг имени' },
  { time: '14:02:12', level: 'success', msg: 'CRC32 рассчитан: A7F3 9E2C' },
  { time: '14:02:13', level: 'info', msg: 'Раздел ПД №5 подраздел ПД №1 ИОС1 ... · извлечение метаданных' },
  { time: '14:02:14', level: 'warn', msg: 'Подпись «Левченко А.И.» не найдена в каталоге, будет пропущена' },
  { time: '14:02:14', level: 'success', msg: 'Excel: лист «АР» заполнен' },
  { time: '14:02:15', level: 'info', msg: 'Excel COM подключен · версия 16.0' },
  { time: '14:02:16', level: 'success', msg: 'PDF экспортирован: ИУЛ_АР_часть4.pdf' },
];

window.IUL_DATA = { SAMPLE_FILES, PERSONS, SIGNATURES, SAMPLE_LOG };
