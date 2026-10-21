#!/bin/bash

set -e

BASE="/opt/project/spammer"
SRC="$BASE/app/backend-new"
DEST="$BASE/backup/backend-new"
DATE=$(date +%Y%m%d-%H%M)
BACKUP="$DEST/$DATE"

mkdir -p "$BACKUP"

echo "===== BACKUP BACKEND NEW ====="
echo "Time: $(date)"

# SQLite consistent backup
sqlite3 "$SRC/fb_manager.db" ".backup '$BACKUP/fb_manager.db'"

# Browser profiles
tar -czf "$BACKUP/fb_profile_1.tar.gz" \
    -C "$SRC" fb_profile_1

tar -czf "$BACKUP/fb_profile_2.tar.gz" \
    -C "$SRC" fb_profile_2

echo "Backup created: $BACKUP"

# Retention: keep 7 days
find "$DEST" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;

echo "Old backups cleaned."
