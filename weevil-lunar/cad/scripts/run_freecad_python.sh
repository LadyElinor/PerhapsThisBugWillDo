#!/usr/bin/env bash
# Use the already-extracted official Linux x86_64 AppImage; no installation.
set -euo pipefail
if [ "$#" -lt 2 ]; then
  echo "Usage: bash run_appimage.sh /path/to/squashfs-root script.py [arguments...]" >&2
  exit 2
fi
fc_root="$(cd "$1" && pwd)"
shift
env PYTHONHOME="$fc_root/usr" PYTHONPATH="$fc_root/usr/lib" \
    LD_LIBRARY_PATH="$fc_root/usr/lib" "$fc_root/usr/bin/python" "$@"
