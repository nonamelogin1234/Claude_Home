# RPG ТРЕКЕР ПРОГРЕССА

## ЦЕЛЬ
Живой дашборд в стиле White Lotus Season 2 (Сицилия) — показывает прогресс тренировок, веса, сна.

## СТАТУС
🟢 Task2 задеплоен — White Lotus тема + анимации водопада

## URL
**https://mcp.myserver-ai.ru:8769/**

## ЧТО СДЕЛАНО
- [2026-04-03] Написан полный код (backend + frontend + Docker) → задеплоен на VPS
- [2026-04-03] FastAPI читает PostgreSQL, UI работает с живыми данными
- [2026-04-11] Task2: White Lotus редизайн — новая тема, шрифты Playfair Display + Lato
- [2026-04-11] Task2: Переименование всего (Практики, Рубежи пути, Этап, Хроника)
- [2026-04-11] Task2: 7 новых квестов (Пятничный ритуал, Без никотина, и др.)
- [2026-04-11] Task2: Анимации — progress-бары, stagger, счётчики чисел, 3D-tilt карточек, ripple, magnetic avatar
- [2026-04-15] Заменил sparse particles → WaterfallCurtain (сплошная завеса)
- [2026-04-15] Gaussian density peaks: 3 плотных зоны водопада по ширине (x=28%, 62%, 82%)
- [2026-04-15] Foam (белая пена), mist (туман), pool surface (анимированная поверхность), sparkles
- [2026-04-15] Hero card min-height: 290px для высоты падения

## СЛЕДУЮЩИЙ ШАГ
- Проверить водопад визуально на живом сайте (пользователь не подтвердил что доволен)
- Возможно: сделать водопад заметнее (увеличить opacity или добавить цветовой контраст)
- Возможно: добавить WebGL/Three.js вариант для максимального качества

## ТЕХНИЧЕСКИЕ ДЕТАЛИ
- Backend: FastAPI, порт 8768 (внутри Docker)
- Docker: network_mode host, postgres по IP 172.18.0.4
- Nginx: /etc/nginx/sites-enabled/rpg-tracker, listen 8769 ssl, cert mcp.myserver-ai.ru
- Деплой: /opt/rpg-tracker/, клон в /tmp/claude_home
- Перезапуск: `cd /tmp/claude_home && git pull origin main && cp -r rpg/frontend /opt/rpg-tracker/ && docker restart rpg-tracker`
- Уровни: Начало (0-10) / На ходу (10-25) / В ритме (25-50) / Форма (50-100) / Образ жизни (100+)
- Рубежи: 110 / 105 / 99 / 90 / 85 кг

## ГРАБЛИ
- Postgres доступен только по IP 172.18.0.4 (VPS не резолвит имена контейнеров вне сети)
- При деплое: docker compose down не всегда удаляет контейнер → `docker rm -f rpg-tracker`
- /tmp/claude_home не существует при первом деплое → сначала git clone, потом git pull
- Canvas-анимация (requestAnimationFrame) зависает preview-рендерер Claude Code → нельзя скриншотить живую анимацию через preview_screenshot
- `bash_tool` при вызове `powershell` — команда не найдена (запускается в WSL) → использовать `mcp__Desktop_Commander__start_process` с `shell: powershell.exe`
