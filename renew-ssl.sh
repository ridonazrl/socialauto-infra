#!/bin/bash
# Script Auto-Renew SSL untuk SocialAuto.tech

echo "=== 1. Stop Nginx Proxy ==="
cd /opt/project/spammer
docker compose stop proxy
sleep 3

echo "=== 2. Renew Certbot ==="
sudo certbot renew --quiet

echo "=== 3. Start Nginx Proxy ==="
docker compose start proxy
sleep 3

echo "=== 4. Reload Nginx (ambil cert baru) ==="
docker compose exec proxy nginx -s reload

echo "=== Selesai ==="
