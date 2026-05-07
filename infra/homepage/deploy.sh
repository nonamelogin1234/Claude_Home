#!/bin/bash
# Deploy script for Homepage + Authelia
# Run on VPS as root

set -e

REPO="https://raw.githubusercontent.com/nonamelogin1234/Claude_Home/main/HomePage"

echo "=== Создаём директории ==="
mkdir -p /opt/homepage/config
mkdir -p /opt/authelia/config

echo "=== Скачиваем конфиги Homepage ==="
curl -sL "$REPO/homepage/docker-compose.yml" -o /opt/homepage/docker-compose.yml
curl -sL "$REPO/homepage/config/services.yaml" -o /opt/homepage/config/services.yaml
curl -sL "$REPO/homepage/config/settings.yaml" -o /opt/homepage/config/settings.yaml
curl -sL "$REPO/homepage/config/widgets.yaml" -o /opt/homepage/config/widgets.yaml

echo "=== Скачиваем конфиги Authelia ==="
curl -sL "$REPO/authelia/docker-compose.yml" -o /opt/authelia/docker-compose.yml
curl -sL "$REPO/authelia/config/configuration.yml" -o /opt/authelia/config/configuration.yml
curl -sL "$REPO/authelia/config/users_database.yml" -o /opt/authelia/config/users_database.yml

echo "=== Генерируем секреты Authelia ==="
JWT_SECRET=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -hex 32)
sed -i "s/CHANGE_ME_JWT_SECRET/$JWT_SECRET/" /opt/authelia/config/configuration.yml
sed -i "s/CHANGE_ME_SESSION_SECRET/$SESSION_SECRET/" /opt/authelia/config/configuration.yml
echo "Секреты заменены."

echo "=== Генерируем хэш пароля для Authelia ==="
echo ""
echo "!!! ВВЕДИТЕ ПАРОЛЬ для пользователя sergei:"
read -s USER_PASSWORD
HASH=$(docker run --rm authelia/authelia:latest authelia hash-password "$USER_PASSWORD" | grep 'Digest:' | awk '{print $2}')
sed -i "s|CHANGE_ME_PASSWORD_HASH|$HASH|" /opt/authelia/config/users_database.yml
echo "Пароль захэширован и записан."

echo "=== Запускаем Homepage ==="
cd /opt/homepage && docker compose pull && docker compose up -d

echo "=== Запускаем Authelia ==="
cd /opt/authelia && docker compose pull && docker compose up -d

echo "=== Скачиваем nginx конфиги (новые) ==="
curl -sL "$REPO/nginx/homepage" -o /etc/nginx/sites-available/homepage
curl -sL "$REPO/nginx/authelia" -o /etc/nginx/sites-available/authelia

echo "=== Скачиваем обновлённые nginx конфиги существующих сервисов ==="
curl -sL "$REPO/nginx/vaultwarden" -o /etc/nginx/sites-available/vaultwarden
curl -sL "$REPO/nginx/music" -o /etc/nginx/sites-available/music
curl -sL "$REPO/nginx/immich" -o /etc/nginx/sites-available/immich

echo "=== Активируем новые конфиги ==="
ln -sf /etc/nginx/sites-available/homepage /etc/nginx/sites-enabled/homepage
ln -sf /etc/nginx/sites-available/authelia /etc/nginx/sites-enabled/authelia
# Существующие конфиги (vaultwarden, music, immich) уже в sites-enabled через симлинки

echo ""
echo "=== СЛЕДУЮЩИЕ ШАГИ (выполнить вручную) ==="
echo ""
echo "1. Убедитесь что DNS записи добавлены в Cloudflare:"
echo "   home.myserver-ai.ru -> 147.45.238.120 (DNS only, не proxied)"
echo "   auth.myserver-ai.ru -> 147.45.238.120 (DNS only, не proxied)"
echo ""
echo "2. Получить SSL сертификаты (после того как DNS распространится):"
echo "   certbot certonly --nginx -d home.myserver-ai.ru"
echo "   certbot certonly --nginx -d auth.myserver-ai.ru"
echo ""
echo "3. Проверить и применить nginx:"
echo "   nginx -t && systemctl reload nginx"
echo ""
echo "4. Войти на https://auth.myserver-ai.ru и настроить TOTP"
echo ""
echo "ВНИМАНИЕ: Vaultwarden и Navidrome за Authelia сломает мобильные клиенты/расширения."
echo "          При необходимости поставить policy: bypass для этих доменов."
echo ""
echo "=== Готово! ==="
