# МОНИТОРИНГ-ДАШБОРД

## ЦЕЛЬ
Self-hosted дашборд мониторинга всей инфраструктуры (VPS + домашний сервер).
Доступен по адресу https://monitor.myserver-ai.ru.

## СТАТУС
🟡 Конфиги готовы, деплой не выполнен

## ЧТО СДЕЛАНО
- [2026-03-29] Созданы все конфиги стека (docker-compose, prometheus, alertmanager, grafana)
- [2026-03-29] Написаны скрипты деплоя setup.sh и homeserver-setup.sh
- [2026-03-29] Написан nginx конфиг для monitor.myserver-ai.ru
- [2026-03-29] Файлы запушены в GitHub

## СЛЕДУЮЩИЙ ШАГ
1. Запустить `setup.sh` на VPS
2. Запустить `homeserver-setup.sh` на домашнем сервере
3. Добавить nginx конфиг и получить/расширить SSL сертификат
4. Вписать Telegram bot_token и chat_id в alertmanager/alertmanager.yml
5. Импортировать дашборды в Grafana: 1860 (Node Exporter Full), 193 (Docker), 9628 (PostgreSQL)

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Стек (на VPS, /opt/monitoring/)
| Сервис | Образ | Порт (внутренний) |
|--------|-------|-------------------|
| Grafana | grafana/grafana:10.4.2 | 127.0.0.1:3000 |
| Prometheus | prom/prometheus:v2.51.0 | 127.0.0.1:9090 |
| Node Exporter (VPS) | prom/node-exporter:v1.8.0 | 127.0.0.1:9100 |
| cAdvisor | gcr.io/cadvisor/cadvisor:v0.49.1 | 127.0.0.1:8080 |
| Postgres Exporter | prometheuscommunity/postgres-exporter:v0.15.0 | 127.0.0.1:9187 |
| Alertmanager | prom/alertmanager:v0.27.0 | 127.0.0.1:9093 |

### Сети Docker
- `monitoring` — внутренняя сеть стека
- `monitoring_net` (external) — для связи postgres-exporter ↔ postgres

### Что мониторится
- VPS: CPU, RAM, диск, сеть, load average
- VPS Docker: n8n, postgres, vaultwarden, wg-easy, tunnel
- VPS systemd: shell-api, docai, kinoclaude, nginx, 3proxy
- PostgreSQL: pg_up, connections, queries (jarvis_memory)
- Домашний сервер: CPU, RAM, диск, сеть (через WireGuard 10.8.0.27:9100)

### Алерты
- TargetDown (2 мин) → critical
- HighCPU > 85% (5 мин) → warning
- HighMemory > 90% (5 мин) → warning
- LowDisk < 15% (10 мин) → warning
- ContainerDown (2 мин) → critical
- PostgreSQLDown (1 мин) → critical
- SystemdServiceFailed (1 мин) → critical
- HomeServerDown (5 мин) → warning
- HighLoadAverage (5 мин) → warning

### SSL
Ожидается wildcard /etc/letsencrypt/live/myserver-ai.ru/fullchain.pem.
Если нет — добавить subdomain: `certbot certonly --nginx -d monitor.myserver-ai.ru`

## ГРАБЛИ
- monitoring_net нужно создать ДО docker compose up
- postgres-exporter должен быть в двух сетях: default (monitoring) + monitoring_net
- Имя контейнера postgres определяется автоматически в setup.sh по expose=5432
- Grafana admin пароль генерируется при первом запуске setup.sh, хранится в /opt/monitoring/.env
