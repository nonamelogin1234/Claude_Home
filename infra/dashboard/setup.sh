#!/bin/bash
# Запускать на VPS от root или sudo
# Деплой стека мониторинга Grafana+Prometheus
set -e

REPO_RAW="https://raw.githubusercontent.com/nonamelogin1234/Claude_Home/main/dashboard"
DIR="/opt/monitoring"

echo "=== [1/6] Создание директорий ==="
mkdir -p "$DIR"/{prometheus/rules,alertmanager,grafana/provisioning/{datasources,dashboards}}

echo "=== [2/6] Скачивание конфигов ==="
curl -fsSL "$REPO_RAW/docker-compose.yml"                                          -o "$DIR/docker-compose.yml"
curl -fsSL "$REPO_RAW/prometheus/prometheus.yml"                                   -o "$DIR/prometheus/prometheus.yml"
curl -fsSL "$REPO_RAW/prometheus/rules/alerts.yml"                                 -o "$DIR/prometheus/rules/alerts.yml"
curl -fsSL "$REPO_RAW/alertmanager/alertmanager.yml"                               -o "$DIR/alertmanager/alertmanager.yml"
curl -fsSL "$REPO_RAW/grafana/provisioning/datasources/prometheus.yaml"            -o "$DIR/grafana/provisioning/datasources/prometheus.yaml"
curl -fsSL "$REPO_RAW/grafana/provisioning/dashboards/provider.yaml"               -o "$DIR/grafana/provisioning/dashboards/provider.yaml"

echo "=== [3/6] Создание .env ==="
if [ ! -f "$DIR/.env" ]; then
    PASS=$(openssl rand -base64 16)
    echo "GRAFANA_PASSWORD=$PASS" > "$DIR/.env"
    echo ">>> Grafana admin пароль: $PASS  (сохрани!)"
else
    echo ".env уже существует, пропускаю"
fi

echo "=== [4/6] Docker сеть monitoring_net ==="
docker network create monitoring_net 2>/dev/null && echo "Сеть создана" || echo "Сеть уже существует"

# Подключаем postgres к monitoring_net (имя контейнера может отличаться)
POSTGRES_CONTAINER=$(docker ps --filter "expose=5432" --format "{{.Names}}" | head -1)
if [ -n "$POSTGRES_CONTAINER" ]; then
    docker network connect monitoring_net "$POSTGRES_CONTAINER" 2>/dev/null \
        && echo "Контейнер $POSTGRES_CONTAINER подключён к monitoring_net" \
        || echo "$POSTGRES_CONTAINER уже в monitoring_net"
else
    echo "ВНИМАНИЕ: контейнер postgres не найден — postgres-exporter не получит метрики"
fi

echo "=== [5/6] Запуск стека ==="
cd "$DIR"
docker compose pull
docker compose up -d

echo "=== [6/6] Статус ==="
docker compose ps

echo ""
echo "========================================="
echo "Grafana: http://127.0.0.1:3000"
echo "Пароль:  $(grep GRAFANA_PASSWORD $DIR/.env | cut -d= -f2)"
echo ""
echo "Осталось:"
echo "  1. Вписать Telegram токен в $DIR/alertmanager/alertmanager.yml"
echo "  2. Настроить nginx (конфиг nginx-monitor.conf из репо)"
echo "  3. Установить node_exporter на homeserver (homeserver-setup.sh)"
echo "  4. Импортировать дашборды: 1860, 193, 9628"
echo "========================================="
