#!/usr/bin/env bash
# Deploy the integration to the HA config share. Only runs when invoked.
# Usage: scripts/deploy.sh [CONFIG_DIR]   (default: /Volumes/config)
set -euo pipefail

CONFIG_DIR="${1:-/Volumes/config}"
SRC="$(cd "$(dirname "$0")/.." && pwd)/custom_components/dingtian"
DEST="$CONFIG_DIR/custom_components/dingtian"

if [ -d "$DEST" ]; then
  # Outside custom_components/: HA scans every folder in there.
  BACKUP_DIR="$CONFIG_DIR/custom_components_backups"
  mkdir -p "$BACKUP_DIR"
  BACKUP="$BACKUP_DIR/dingtian.bak-$(date +%Y%m%d-%H%M%S)"
  cp -R "$DEST" "$BACKUP"
  echo "Backed up $DEST to $BACKUP"
fi

mkdir -p "$DEST"
# cp -f per file: rsync fails on the Samba share.
(cd "$SRC" && find . -type f ! -name '*.pyc' ! -path '*/__pycache__/*' | while read -r f; do
  mkdir -p "$DEST/$(dirname "$f")"
  cp -f "$SRC/$f" "$DEST/$f"
done)

echo "Deployed. Fully RESTART Home Assistant (a reload keeps old Python modules), then refresh the browser."
