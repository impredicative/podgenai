#!/usr/bin/env bash
set -euo pipefail

SR=24000
CHANNELS=1
BITRATE="160k"
REQ_DUR=0.50
OUTPUT_FILE="./src/podgenai/audio/pause-${REQ_DUR}s.mp3"

ffmpeg -hide_banner -y \
  -f lavfi -i "anullsrc=r=${SR}:cl=mono" \
  -t "${REQ_DUR}" \
  -c:a libmp3lame \
  -b:a "${BITRATE}" \
  -ar "${SR}" \
  -ac "${CHANNELS}" \
  -write_xing 0 \
  "${OUTPUT_FILE}"

ffprobe -v error \
  -select_streams a:0 \
  -show_entries stream=codec_name,codec_type,sample_rate,channels,channel_layout,time_base \
  -of default=noprint_wrappers=1 \
  "${OUTPUT_FILE}"