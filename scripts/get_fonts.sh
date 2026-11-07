#!/usr/bin/env bash
# Download IBM Plex Sans Thai (SIL Open Font License), used for figure text.
# Its Latin glyphs are those of IBM Plex Sans. Without it, figures fall back to DejaVu Sans.
set -euo pipefail
dir="$(cd "$(dirname "$0")/.." && pwd)/fonts"
mkdir -p "$dir"
base="https://github.com/google/fonts/raw/main/ofl/ibmplexsansthai"
for f in Regular Medium SemiBold Bold Light; do
  curl -sSfL -o "$dir/IBMPlexSansThai-$f.ttf" "$base/IBMPlexSansThai-$f.ttf"
done
curl -sSfL -o "$dir/OFL.txt" "$base/OFL.txt"
echo "fonts saved to $dir"
