#!/bin/bash
# Запускать на домашнем сервере (homeserver, user: sergei)
# Устанавливает Node Exporter + открывает порт для VPS через WireGuard
set -e

VERSION="1.8.0"
ARCH="linux-amd64"
VPS_WG_IP="10.8.0.1"

echo "=== [1/4] Скачивание Node Exporter v$VERSION ==="
cd /tmp
curl -LO "https://github.com/prometheus/node_exporter/releases/download/v${VERSION}/node_exporter-${VERSION}.${ARCH}.tar.gz"
tar xzf "node_exporter-${VERSION}.${ARCH}.tar.gz"
sudo cp "node_exporter-${VERSION}.${ARCH}/node_exporter" /usr/local/bin/
sudo chmod +x /usr/local/bin/node_exporter
rm -rf "node_exporter-${VERSION}.${ARCH}"*

echo "=== [2/4] Создание systemd сервиса ==="
sudo tee /etc/systemd/system/node-exporter.service > /dev/null << 'UNIT'
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=nobody
ExecStart=/usr/local/bin/node_exporter \
  --web.listen-address=0.0.0.0:9100
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable node-exporter
sudo systemctl start node-exporter

echo "=== [3/4] Открытие порта 9100 для VPS (через WireGuard) ==="
sudo ufw allow in on wg1 to any port 9100 comment "Prometheus from VPS WireGuard" 2>/dev/null \
    || sudo ufw allow from "$VPS_WG_IP" to any port 9100 comment "Prometheus from VPS"

echo "=== [4/4] Проверка ==="
sudo systemctl status node-exporter --no-pager
echo ""
echo "Node Exporter слушает:"
ss -tlnp | grep 9100
