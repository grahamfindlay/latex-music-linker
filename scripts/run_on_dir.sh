#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 INPUT_DIR OUTPUT_DIR" >&2
  exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

mkdir -p "$OUTPUT_DIR"

for f in "$INPUT_DIR"/*.tex; do
  base="$(basename "$f")"
  latex-music-linker "$f" "$OUTPUT_DIR/$base"
done
