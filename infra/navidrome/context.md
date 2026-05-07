# NAVIDROME — ПЕРСОНАЛЬНЫЙ МУЗЫКАЛЬНЫЙ СТРИМИНГ

## ЦЕЛЬ
Navidrome на домашнем сервере, доступный снаружи через nginx на VPS.
Subsonic API для мобильных клиентов (Symfonium и др.).

## СТАТУС
🟢 Готово — https://music.myserver-ai.ru работает

## ЧТО СДЕЛАНО
- [2026-04-04] Установлен Navidrome v0.61.0 как systemd-сервис на домашнем сервере → active (running)
- [2026-04-04] Папка с музыкой: /srv/jellyfin/Music (Samba Z:\Music, тот же диск что Films/Series)
- [2026-04-04] Добавлена DNS A-запись music.myserver-ai.ru → 147.45.238.120 в Cloudflare
- [2026-04-04] Выпущен Let's Encrypt сертификат (ECC) через acme.sh
- [2026-04-04] Задеплоен nginx конфиг на VPS: music.myserver-ai.ru → 10.8.0.27:4533 через WireGuard
- [2026-04-04] Проверка: HTTP 200, Subsonic API отвечает
- [2026-04-04] Добавлен ReverseProxyWhitelist = 10.8.0.0/24 (Navidrome знает что за HTTPS прокси)
- [2026-04-04] DNS переключён на grey cloud (DNS only) — браузер коннектится напрямую к VPS

## СЛЕДУЮЩИЙ ШАГ
1. Открыть http://192.168.0.103:4533/app/ → создать admin-пользователя
2. После этого https://music.myserver-ai.ru/app/ заработает полностью
3. В Symfonium: Add provider → Navidrome → URL: https://music.myserver-ai.ru
4. Залить музыку в Z:\Music\ — Navidrome подхватит автоматически

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Домашний сервер
- Бинарь: `/usr/local/bin/navidrome`
- Конфиг: `/home/sergei/navidrome.toml`
- Музыка: `/srv/jellyfin/Music/` (Samba-шара Z:\, рядом с Films и Series)
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

# Залить музыку (с Windows) — прямо в Z:\Music\ через проводник или rsync
# rsync через SSH:
rsync -av "/c/Music/" sergei@192.168.0.103:/srv/jellyfin/Music/

# Subsonic API ping (после создания пользователя)
curl "https://music.myserver-ai.ru/rest/ping.view?u=admin&p=ПАРОЛЬ&v=1.16.0&c=test&f=json"

# Перезапуск
sudo systemctl restart navidrome
```

## ГРАБЛИ
- ZeroSSL отклоняет домен при Cloudflare proxy → использовать `--server letsencrypt`
- acme.sh через srv.ps1 запускать через `bash -c '...'` — иначе ошибка пути
- Белый экран через nginx: Navidrome не знал что за HTTPS → ReverseProxyWhitelist = "10.8.0.0/24"
- Cloudflare Rocket Loader ломает React SPA → grey cloud (DNS only) для music поддомена
- Symfonium: выбирать Navidrome/Subsonic, НЕ WebDAV
