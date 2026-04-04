# Navidrome — Персональный музыкальный стриминг

## Цель
Развернуть Navidrome на домашнем сервере (Maibenben) и открыть его наружу через уже существующий nginx на VPS + WireGuard туннель. Получить рабочий веб-интерфейс и Subsonic API для мобильных клиентов.

## Контекст инфраструктуры
- Домашний сервер: Ubuntu Server 24.04, user `sergei`, IP в сети WireGuard `10.8.0.27`, shell через `home.ps1`
- VPS: `myserver-ai.ru`, nginx уже проксирует другие сервисы домашнего сервера (Immich → `10.8.0.27:2283`, Nextcloud → `10.8.0.27:8181`) — по той же схеме делать Navidrome
- WireGuard туннель между VPS и домашним сервером уже работает (wg1, порт 51822)
- Cloudflare DNS управляет доменом `myserver-ai.ru`

## Задача

### 1. Navidrome на домашнем сервере
- Установить Navidrome как systemd-сервис (не Docker — сервер маломощный, 8GB RAM, уже есть Immich и Nextcloud)
- Если Docker предпочтительнее по изоляции — на усмотрение Claude Code, но обосновать
- Порт: любой свободный (предлагаю 4533 — дефолтный для Navidrome)
- Папка с музыкой: `/home/sergei/music` (создать если нет)
- Папка с данными Navidrome (БД, кеш): `/home/sergei/navidrome-data`
- Конфиг: `/home/sergei/navidrome.toml` или через env в systemd unit

### 2. Nginx на VPS — новый маршрут
По аналогии с Immich (`photos.myserver-ai.ru` → `10.8.0.27:2283`) добавить:
- Домен: `music.myserver-ai.ru`
- Проксировать на: `10.8.0.27:4533`
- HTTPS через Cloudflare (режим Full или Full Strict — как у остальных)
- Добавить в nginx конфиг на VPS новый server block

### 3. DNS
- Добавить A-запись `music.myserver-ai.ru` → `147.45.238.120` в Cloudflare (или проверить что уже есть wildcard)
- Если есть wildcard `*.myserver-ai.ru` — дополнительных действий не нужно, просто уточнить

### 4. Проверка
- `https://music.myserver-ai.ru` открывается, показывает страницу входа Navidrome
- Войти под admin, убедиться что интерфейс работает
- Проверить что Subsonic API отвечает: `https://music.myserver-ai.ru/rest/ping.view?u=admin&p=PASSWORD&v=1.16.0&c=test&f=json`

## Что НЕ входит в задачу
- Заливка музыки (это Сергей сделает сам через rsync)
- Настройка мобильных клиентов (Symfonium и т.п.) — после того как сервер заработает
- Last.fm интеграция — опционально потом

## Результат
Файлы/изменения которые должны быть сделаны:
1. Установка и конфиг Navidrome на домашнем сервере
2. Systemd unit файл (или docker-compose если выбран Docker)
3. Новый server block в nginx на VPS для `music.myserver-ai.ru`
4. Краткая инструкция: как добавлять музыку (rsync команда), как создать дополнительного пользователя
