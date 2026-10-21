#!/bin/bash
# ============================================
# START ALL — Auto-Like & Auto-Comment
# VPS: srv2040759 (10.10.100.10 / 187.77.119.183)
# ============================================

set -e

echo "=== 1. RESTART DOCKER ==="
systemctl restart docker
sleep 10
systemctl status docker --no-pager | head -3

echo ""
echo "=== 2. START SEMUA SERVICE ==="
cd /opt/project/spammer
docker compose up -d
sleep 10

echo ""
echo "=== 3. STATUS CONTAINER ==="
docker compose ps

echo ""
echo "=== 4. VERIFIKASI HEALTH (API & Web) ==="
echo -n "Auto-Comment BE: "
curl -s --max-time 5 http://127.0.0.1:8000/status | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"OK - {d['accounts_count']} akun, gemini={d['has_gemini_api_key']}\")" 2>/dev/null || echo "FAILED"

echo -n "Auto-Like BE:    "
curl -s --max-time 5 http://127.0.0.1:8081/api/config >/dev/null 2>&1 && echo "OK" || echo "FAILED"

echo -n "Auto-Like FE:    "
curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8082/ && echo " OK" || echo " FAILED"

echo -n "Auto-Comment FE: "
curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:5175/ && echo " OK" || echo " FAILED"

echo ""
echo "=== SELESAI ==="
echo "Untuk cek koneksi ke Chrome Windows via Tailscale, jalankan:"
echo "  /opt/project/spammer/check-cdp.sh"
echo ""
echo "Auto-Like FE:    http://187.77.119.183:8082/"
echo "Auto-Comment FE: http://187.77.119.183:5175/"
