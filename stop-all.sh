#!/bin/bash
# ============================================
# STOP ALL — Auto-Like & Auto-Comment
# ============================================

echo "=== STOP SEMUA SERVICE ==="
cd /opt/project/spammer
docker compose down

echo ""
echo "=== STATUS ==="
docker compose ps
echo "Semua service dihentikan."
