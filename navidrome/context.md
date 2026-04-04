# NAVIDROME — ПЕРСОНАЛЬНЫЙ МУЗЫКАЛЬНЫЙ СТРИМИНГ

## ЦЕЛЬ
Navidrome на домашнем сервере, доступный снаружи через nginx на VPS.
Subsonic API для мобильных клиентов (Symfonium и др.).

## СТАТУС
🟢 Готово — https://music.myserver-ai.ru работает

## ЧТО СДЕЛАНО
- [2026-04-04] Установлен Navidrome v0.61.0 как systemd-сервис на домашнем сервере → active (running)
- [2026-04-04] Добавлена DNS A-запись music.myserver-ai.ru → 147.45.238.120 в Cloudflare
- [2026-04-04] Выпущен Let's Encrypt сертификат (ECC) через acme.sh
- [2026-04-04] Задеплоен nginx конфиг на VPS: music.myserver-ai.ru → 10.8.0.27:4533 через WireGuard
- [2026-04-04] Проверка: HTTP 200, Subsonic API отвечает

## СЛЕДУЮЩИЙ ШАГ
1. Открыть https://music.myserver-ai.ru — создать admin-пользователя (первый вход)
2. Залить музыку: `rsync -av /путь/к/музыке/ sergei@homeserver:/home/sergei/music/`
3. Настроить мобильный клиент (Symfonium): сервер = https://music.myserver-ai.ru

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Домашний сервер
- Бинарь: `/usr/local/bin/navidrome`
- Конфиг: `/home/sergei/navidrome.toml`
- Музыка: `/home/sergei/music/`
- Данные/БД: `/home/sergei/navidrome-data/`
- Порт: `4533`
- Сервис: `systemctl status navidrome`

### VPS
- Nginx конфиг: `/etc/nginx/sites-available/music`
- SSL сертификат: `/.acme.sh/music.myserver-ai.ru_ecc/`
- Автообновление: acme.sh cron уже настроен глобально

### Команды
```bash
# Статус
systemctl status navidrome          # на домашнем сервере

# Залить музыку (с Windows)
rsync -av "C:\Music\" sergei@homeserver:/home/sergei/music/

# Subsonic API ping (после создания пользователя)
curl "https://music.myserver-ai.ru/rest/ping.view?u=admin&p=ПАРОЛЬ&v=1.16.0&c=test&f=json"

# Перезапуск
sudo systemctl restart navidrome
```

## ГРАБЛИ
- ZeroSSL отклоняет домен при Cloudflare proxy → использовать `--server letsencrypt`
- acme.sh через srv.ps1 запускать через `bash -c '...'` — иначе ошибка пути
