#!/usr/bin/env bash

set -euo pipefail

# Check argument count
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 /path/to/file.mp3"
    exit 1
fi

FILE="$1"

# Check file exists
if [[ ! -f "$FILE" ]]; then
    echo "Error: File does not exist: $FILE"
    exit 1
fi

# Check ffprobe is available
if ! command -v ffprobe >/dev/null 2>&1; then
    echo "Error: ffprobe is not installed or not in PATH."
    exit 1
fi

# Print audio stream info
ffprobe -v error \
  -select_streams a:0 \
  -show_entries stream=codec_name,codec_long_name,profile,sample_rate,channels,channel_layout,bit_rate \
  -of default=noprint_wrappers=1 \
  "$FILE"