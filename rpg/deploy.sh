#!/bin/bash
set -e

echo "=== RPG Tracker Deploy ==="

# Create dir
mkdir -p /opt/rpg-tracker

# Clone/update from GitHub
if [ -d /tmp/claude_home ]; then
    cd /tmp/claude_home && git pull
else
    git clone https://github.com/nonamelogin1234/Claude_Home /tmp/claude_home
fi

# Copy files
cp -r /tmp/claude_home/rpg/backend /opt/rpg-tracker/
cp -r /tmp/claude_home/rpg/frontend /opt/rpg-tracker/
cp /tmp/claude_home/rpg/docker-compose.yml /opt/rpg-tracker/

# Build and start
cd /opt/rpg-tracker
docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo "=== Checking if nginx has /rpg location ==="
if ! grep -q "rpg" /etc/nginx/sites-enabled/default 2>/dev/null && ! grep -q "rpg" /etc/nginx/conf.d/*.conf 2>/dev/null; then
    echo "Adding nginx config..."
    # Add to nginx config - find the main server block file
    NGINX_CONF=$(grep -rl "myserver-ai.ru" /etc/nginx/ 2>/dev/null | head -1)
    if [ -n "$NGINX_CONF" ]; then
        echo "Found nginx config: $NGINX_CONF"
        # Insert before last closing brace
        python3 -c "
content = open('$NGINX_CONF').read()
snippet = '''
    # RPG Tracker
    location /rpg/ {
        proxy_pass http://127.0.0.1:8768/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 30s;
    }
'''
# Insert before last closing brace
idx = content.rfind('}')
new_content = content[:idx] + snippet + content[idx:]
open('$NGINX_CONF', 'w').write(new_content)
print('nginx config updated')
"
        nginx -t && nginx -s reload && echo "nginx reloaded"
    fi
fi

echo "=== Done! ==="
echo "RPG Tracker available at: https://myserver-ai.ru/rpg/"
docker ps | grep rpg
