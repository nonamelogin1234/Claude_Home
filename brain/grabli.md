# ГРАБЛИ — ЗАПОМНИТЬ НАВСЕГДА

## PowerShell / Windows

- `shell:run_command` возвращает null — это нормально, команда выполнилась
- `bash_tool` пишет файлы В КОНТЕЙНЕР, не на ПК → для ПК использовать `Desktop Commander:write_file`
- `bash_tool` НЕ работает для команд на сервере — только через srv.ps1/home.ps1
- `-SkipCertificateCheck` не работает в PowerShell 5 → заменять на `[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }`
- `srv.ps1` ломает сложные команды с кавычками и кириллицей → большие файлы через GitHub → curl
- heredoc через PowerShell не записывается в файл → использовать `python3 -c "open(...).write(...)"`
- **Кириллица в выводе srv.ps1 — кракозябры, это НОРМАЛЬНО. Не пытаться чинить.**

## GitHub

- Блокирует push если в файле есть Google OAuth access_token → передавать через SCP
- Raw кэширует ~10 мин → для срочного деплоя SCP напрямую
- **Редактировать файлы в GitHub — только `github:get_file_contents` + `github:create_or_update_file`**
- При push нескольких файлов сразу — использовать `github:push_files`, лимит ~5 файлов за раз

## Git на локальном компе

- Никогда не клонировать репо ВНУТРЬ другого клонированного репо — будет submodule и git не видит файлы
- Если скачиваешь с GitHub как zip — .git внутри нет, файлы копируются нормально
- Если клонируешь через git clone — внутри будет .git, нельзя вкладывать в другой git репо

## VPS / Docker / n8n

- VPS не резолвит свой домен изнутри → использовать IP 147.45.238.120 напрямую
- `executeCommand` в n8n выполняется ВНУТРИ Docker → всегда HTTP Request → Shell API `http://172.18.0.1:7722`
- wg0 на хосте VPS конфликтует с wg-easy → `sudo wg-quick down wg0 && sudo docker start wg-easy`

## Claude Code

- Claude Code Desktop SSH на Windows — НЕ РАБОТАЕТ, известный баг. Не тратить время.
- `--dangerously-skip-permissions` заблокирован для root → нужен не-root пользователь
- claude авторизуется через OAuth (браузер) — в SSH без port forwarding не работает
- API ключ не подходит если только Pro подписка (нет Console аккаунта)
- Node.js v12 (системный Ubuntu) слишком старый → нужен v20+

## Домашний сервер

- AdGuard Home УДАЛЁН (2026-03-22) — не пытаться переподключать
- SSH с домашнего ПК не работает при включённом WireGuard VPN → отключать WireGuard перед SSH
- SMB шара на русской Windows: "Everyone" не работает → использовать `$env:USERNAME` или "Все"
- Windows локальные пользователи не могут войти по сети из-за политики ForceGuest → фикс: `Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "ForceGuest" -Value 0`
- `$`-переменные nginx (например `$host`) теряются при передаче через home.ps1 → использовать `printf` вместо python3/heredoc
- Сетевой диск, примонтированный в admin PowerShell, НЕ виден в обычном Explorer — `EnableLinkedConnections` не всегда помогает → монтировать через скрипт автозапуска от имени обычного пользователя
- Скорость SMB упирается в 100Мбит (~11 МБ/с) если роутер/порт не гигабитный

## Hevy / Health Connect

- `hevy_sets` — новая таблица (25.03.2026), каждый подход отдельной строкой
- Единицы energy в Health Connect — миллиКалории (mcal), делить на 1000
