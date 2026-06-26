#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="rsshmount-windows-amd64"
TMP="$(mktemp -d)"
DIST="$TMP/$NAME"

cleanup() {
  rm -rf "$TMP"
}
trap cleanup EXIT

mkdir -p "$DIST/bin" "$ROOT/dist"

cp "$ROOT/rsshmount.py" "$DIST/rsshmount.py"
cp "$ROOT/rsshmount_gui.pyw" "$DIST/rsshmount_gui.pyw"
cp "$ROOT/rsshmount.cmd" "$DIST/rsshmount.cmd"
cp "$ROOT/rsshmount-gui.cmd" "$DIST/rsshmount-gui.cmd"
cp "$ROOT/install.ps1" "$DIST/install.ps1"
cp "$ROOT/install-windows-deps.ps1" "$DIST/install-windows-deps.ps1"
mkdir -p "$DIST/scripts"
cp "$ROOT/scripts/build-windows-exe.ps1" "$DIST/scripts/build-windows-exe.ps1"
cp "$ROOT/README.md" "$DIST/README.md"

curl -fsSL "https://downloads.rclone.org/rclone-current-windows-amd64.zip" -o "$TMP/rclone.zip"
unzip -q "$TMP/rclone.zip" -d "$TMP"
RCLONE_DIR="$(find "$TMP" -maxdepth 1 -type d -name 'rclone-*-windows-amd64' | head -n 1)"
test -n "$RCLONE_DIR"
cp "$RCLONE_DIR/rclone.exe" "$DIST/bin/rclone.exe"

python3 - "$ROOT/dist/$NAME.zip" "$DIST" "$NAME" <<'PY'
import os
import sys
import zipfile
from pathlib import Path

target = Path(sys.argv[1])
source = Path(sys.argv[2])
root_name = sys.argv[3]

with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
    for path in source.rglob("*"):
        if path.is_file():
            zf.write(path, Path(root_name) / path.relative_to(source))
print(target)
PY
