# Подключение к серверам

## Рабочий ПК (torganov-a)

### Клод запускает команды на VPS
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\torganov-a\srv.ps1 -cmd "КОМАНДА"
```

### Клод запускает команды на домашнем сервере
Напрямую через home.ps1 (апрель 2026, настроен):
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\torganov-a\home.ps1 -cmd "КОМАНДА"
```

### SSH для Сергея — VPS
```
ssh -i C:\Users\torganov-a\.ssh\id_ed25519 root@147.45.238.120
```

### SSH для Сергея — домашний сервер
```
ssh -i C:\Users\torganov-a\.ssh\id_ed25519 -J root@147.45.238.120 sergei@10.8.0.27
```
Или через алиасы (SSH config настроен):
```
ssh vps
ssh homeserver
```

---

## Домашний ПК (user)

### Клод запускает команды на VPS
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\user\srv.ps1 -cmd "КОМАНДА"
```

### Клод запускает команды на домашнем сервере
Напрямую, VPS не нужен:
```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\user\home.ps1 -cmd "КОМАНДА"
```

### SSH для Сергея — VPS
```
ssh root@147.45.238.120
```

### SSH для Сергея — домашний сервер
```
ssh sergei@192.168.0.106
```
⚠️ Если включён WireGuard VPN — отключи перед подключением.

---

## Справочно

- Shell API VPS напрямую: `POST https://mcp.myserver-ai.ru:7723`, `X-Secret: shell-api-secret-2026`
- Shell API домашнего сервера: `POST https://mcp.myserver-ai.ru:7724`, `X-Secret: home-shell-secret-2026`
- Порт 7724 — shell API домашнего сервера, НЕ SSH
- nginx на VPS без модуля stream — прямое TCP-проксирование SSH не работает
- home.ps1 есть на ОБОИХ ПК (рабочем и домашнем)
