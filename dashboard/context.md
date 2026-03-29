# МОНИТОРИНГ-ДАШБОРД

## ЦЕЛЬ
Self-hosted дашборд мониторинга всей инфраструктуры (VPS + домашний сервер).
Доступен по адресу https://monitor.myserver-ai.ru.

## СТАТУС
🟡 Стек работает, нужны DNS запись + Telegram токен

## ЧТО СДЕЛАНО
- [2026-03-29] Созданы все конфиги стека (docker-compose, prometheus, alertmanager, grafana)
- [2026-03-29] Деплой выполнен: 6 контейнеров на VPS, все targets up
- [2026-03-29] node_exporter установлен на homeserver (10.8.0.27:9100), scraping работает
- [2026-03-29] Импортированы дашборды: 1860 (Node Exporter Full), 193 (Docker), 9628 (PostgreSQL)
- [2026-03-29] nginx настроен для HTTP на port 80, ожидает DNS запись

## СЛЕДУЮЩИЙ ШАГ
1. **DNS**: добавить A-запись `monitor.myserver-ai.ru → 147.45.238.120`
2. **SSL**: после DNS записи запустить:
   `snap run certbot --nginx -d monitor.myserver-ai.ru --non-interactive --agree-tos -m admin@myserver-ai.ru`
3. **Telegram**: вписать токен в `/opt/monitoring/alertmanager/alertmanager.yml` и `docker restart alertmanager`

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Стек (на VPS, /opt/monitoring/)
| Сервис | Образ | Порт | Статус |
|--------|-------|------|--------|
| Grafana | grafana/grafana:10.4.2 | 127.0.0.1:3000 | ✅ Up |
| Prometheus | prom/prometheus:v2.51.0 | 127.0.0.1:9090 | ✅ Up |
| Node Exporter (VPS) | prom/node-exporter:v1.8.0 | 127.0.0.1:9100 | ✅ Up |
| cAdvisor | gcr.io/cadvisor/cadvisor:v0.49.1 | 127.0.0.1:8080 | ✅ Up |
| Postgres Exporter | prometheuscommunity/postgres-exporter:v0.15.0 | 127.0.0.1:9187 | ✅ Up |
| Alertmanager | prom/alertmanager:v0.27.0 | 127.0.0.1:9093 | ✅ Up (blackhole) |

### Grafana
- URL (HTTP): http://monitor.myserver-ai.ru (DNS ещё не добавлен)
- Login: admin
- Password: `gJE91xehVX8QbcCobJEJ0w==` (в /opt/monitoring/.env)
- Дашборды: Node Exporter Full, Docker monitoring, PostgreSQL Database

### Prometheus targets (5/5 up)
- prometheus (localhost:9090)
- node-vps (node-exporter:9100)
- cadvisor-vps (cadvisor:8080)
- postgres (postgres-exporter:9187)
- node-homeserver (10.8.0.27:9100) — через WireGuard

### Сети Docker
- `monitoring` — внутренняя сеть стека
- `monitoring_net` (external) — связь postgres-exporter ↔ postgres контейнер

### Алерты (в prometheus/rules/alerts.yml)
- TargetDown, HighCPU, HighMemory, LowDisk, ContainerDown
- PostgreSQLDown, SystemdServiceFailed, HomeServerDown, HighLoadAverage
- Alertmanager сейчас в режиме blackhole (без Telegram), ждёт токен

## ГРАБЛИ
- monitoring_net нужно создать ДО docker compose up
- postgres-exporter должен быть в двух сетях: default (monitoring) + monitoring_net
- chat_id: 0 — alertmanager считает его пустым, нужно реальное значение (int64)
- certbot 1.21.0 сломан системный, использовать snap-версию
