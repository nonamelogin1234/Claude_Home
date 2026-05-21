# Windows zapret / DNS Geohide / OpenAI — 2026-05-21

## Что обсуждали

- Нужно, чтобы ChatGPT и Codex работали без полного VPN.
- DNS Geohide `hosts`, скачанный вручную в `Downloads\hosts`, ломал ChatGPT/Codex: старые IP (`45.155.204.190`, `37.230.192.51`) давали Cloudflare `403/421`.
- Zapret нужен для Discord/YouTube и пользовательских сайтов, но OpenAI-домены должны быть аккуратно согласованы с DNS Geohide.
- Пользователь попросил привести управление обходом к понятным ярлыкам на рабочем столе.

## Что решили

- Основной режим: `Включить обход` скачивает свежий GeoHide hosts из `Internet-Helper/GeoHideDNS`, ставит его в Windows `hosts`, обновляет OpenAI/ChatGPT/Codex исключения zapret, запускает службу `zapret` и чистит DNS-кэш.
- `Выключить обход` останавливает `zapret`, переводит службу в Manual, ставит минимальный hosts и чистит DNS-кэш.
- `Добавить сайт в обход` интерактивно добавляет домены в `list-general-user.txt`; OpenAI/ChatGPT/Codex защищены от случайного добавления в общий zapret-список.
- Для Codex использовать `https://chatgpt.com/codex`; `codex.openai.com` не считать основной точкой входа.
- Для некоторых сайтов одной записи домена мало: нужны `www.*`, redirect-домены и CDN-домены.

## Что сделали

- Созданы локальные скрипты в `C:\zapret-flowseal\current\`:
  - `enable_bypass.cmd` / `enable_bypass.ps1`
  - `disable_bypass.cmd` / `disable_bypass.ps1`
  - `add_site_bypass.cmd`
  - `check_openai_geohide.cmd` / `check_openai_geohide.ps1`
  - `test_pornhub_strategies.cmd` / `test_pornhub_strategies.ps1`
- На рабочем столе оставлены 3 ярлыка:
  - `Включить обход`
  - `Выключить обход`
  - `Добавить сайт в обход`
- Сделаны кастомные иконки в `C:\zapret-flowseal\current\icons\`:
  - `enable_bypass.ico` — зелёный щит
  - `disable_bypass.ico` — красный щит
  - `add_site_bypass.ico` — синий глобус с плюсом
- Для Pornhub добавлены домены:
  - `pornhub.com`, `www.pornhub.com`
  - `pornhub.org`, `www.pornhub.org`, `rt.pornhub.org`
  - `phncdn.com`, `ei.phncdn.com`, `ew.phncdn.com`
  - `trafficjunky.net`, `www.trafficjunky.net`
- Подобрана рабочая стратегия zapret: `general (ALT11).bat`.
- Проверка после ALT11:
  - `https://www.pornhub.com/` отвечает `301` на `https://rt.pornhub.org/`
  - `https://rt.pornhub.org/` отвечает `200 OK`

## Грабли

- Windows `hosts` сильнее VPN: если OpenAI прибит к плохому Geohide IP, VPN не спасает.
- Старый скачанный `Downloads\hosts` может протухать; для включения обхода нужно скачивать свежий GeoHide hosts.
- `general (ALT).bat` сбрасывал TLS на Pornhub; `general (ALT11).bat` сработал.
- Скрипт добавления сайтов больше не должен срезать `www.`, потому что hostlist может требовать явное `www.*`.

## Следующий шаг

- В новом чате проверить в браузере, что ChatGPT/Codex работают без VPN после `Включить обход`.
- Если какой-то сайт не обходит, добавлять не только основной домен, но и `www`, redirect-домен и CDN-домены; при TLS reset пробовать стратегию, а не только список.
