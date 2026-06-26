#!/usr/bin/env bash
set -euo pipefail

PREFIX="${1:-$HOME/.local}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPDIR="$PREFIX/lib/rsshmount"

mkdir -p "$APPDIR" "$PREFIX/bin"
cp "$SRC/rsshmount" "$APPDIR/rsshmount"
rm -rf "$APPDIR/bin"
cp -R "$SRC/bin" "$APPDIR/bin"
chmod +x "$APPDIR/rsshmount" "$APPDIR/bin/rclone"
ln -sf "$APPDIR/rsshmount" "$PREFIX/bin/rsshmount"

echo "installed: $PREFIX/bin/rsshmount"
