#!/bin/bash
# ============================================
# CHECK CDP — dari VPS ke Windows via Tailscale
# ============================================

WINDOWS_IP="100.114.140.47"

echo "=== 1. TAILSCALE STATUS ==="
tailscale status
echo ""

echo "=== 2. PING WINDOWS (Tailscale) ==="
tailscale ping -c 3 $WINDOWS_IP 2>&1 | head -5
echo ""

echo "=== 3. TEST CDP DARI VPS (host) ==="
for port in 9222 9223 9224 9225 9226; do
  echo -n "CDP $port: "
  result=$(curl -s --max-time 5 http://$WINDOWS_IP:$port/json/version 2>/dev/null)
  if [ -n "$result" ]; then
    browser=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('Browser','?'))" 2>/dev/null)
    echo "OK - $browser"
  else
    echo "FAILED"
  fi
done
echo ""

echo "=== 4. TEST CDP DARI DALAM CONTAINER ==="
docker exec -i auto-like-be python - <<'PY'
import urllib.request, json
WINDOWS_IP = "100.114.140.47"
for port in range(9222, 9227):
    try:
        r = urllib.request.urlopen(f"http://{WINDOWS_IP}:{port}/json/version", timeout=5)
        d = json.loads(r.read())
        print(f"CDP {port}: OK - {d.get('Browser')}")
    except Exception as e:
        print(f"CDP {port}: ERROR - {e}")
PY
echo ""

echo "=== 5. HTTP DETAIL PER PORT ==="
for port in 9222 9223 9224 9225 9226; do
  echo -n "  Port $port: "
  curl -s -o /dev/null -w "HTTP %{http_code} | Time %{time_total}s\n" --max-time 5 http://$WINDOWS_IP:$port/json/version || echo "FAILED"
done
echo ""

echo "=== SELESAI ==="
