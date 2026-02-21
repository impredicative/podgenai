#!/usr/bin/env bash
set -euo pipefail

# Generate a silent MP3 file of a specified duration to be used as a pause in TTS-generated speech. This is necessary because the TTS generator itself does not reliably interpret instructions to insert pauses.
# Confirm generated pause duration at https://metadataview.com/
# View generated pause spectrum at https://www.dcode.fr/spectral-analysis

# =========================
# Hardcoded parameters
# =========================
SR=24000          # Sample rate (Hz)
CHANNELS=1        # Mono (single channel)
BITRATE="160k"    # Constant bitrate
REQ_DUR=0.7       # Requested pause duration (seconds)
OUTPUT_FILE="./src/podgenai/audio/pause${REQ_DUR}s.mp3"  # Output file path

# MP3 Layer III structure
MP3_FRAME_SAMPLES=1152
GRANULE_SAMPLES=576   # 2 granules per MP3 frame

# =========================
# Derive frame counts
# =========================
# Nearest whole MP3 frame count for the requested duration:
# mp3_frames = round(REQ_DUR * SR / 1152)
MP3_FRAMES="$(awk -v d="$REQ_DUR" -v sr="$SR" -v fs="$MP3_FRAME_SAMPLES" \
  'BEGIN { printf "%.0f", (d*sr/fs) + 0.5 }')"

# In this FFmpeg+libmp3lame setup, -frames:a is effectively counting 576-sample granules.
# Therefore, granules = mp3_frames * 2
FRAMES=$(( MP3_FRAMES * 2 ))

if [ "$MP3_FRAMES" -lt 1 ]; then
  echo "Error: computed MP3_FRAMES < 1; check REQ_DUR." >&2
  exit 1
fi

# Derived actual coded duration in seconds (based on MP3 frames)
ACT_DUR="$(awk -v f="$MP3_FRAMES" -v sr="$SR" -v fs="$MP3_FRAME_SAMPLES" \
  'BEGIN { printf "%.6f", (f*fs)/sr }')"

# Expected duration from granules (what -frames:a is limiting)
EXPECTED_CODED_DUR="$(awk -v n="$FRAMES" -v sr="$SR" -v gs="$GRANULE_SAMPLES" \
  'BEGIN { printf "%.6f", (n*gs)/sr }')"

# # =========================
# # Create output directory
# # =========================
# mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "Requested duration:      ${REQ_DUR}s"
echo "Using MP3 frames:        ${MP3_FRAMES} (each ${MP3_FRAME_SAMPLES} samples)"
echo "Using granules (-frames): ${FRAMES} (each ${GRANULE_SAMPLES} samples)"
echo "Actual coded duration:   ${ACT_DUR}s"
echo "Expected coded duration: ${EXPECTED_CODED_DUR}s"
echo

# =========================
# Generate silence MP3
# =========================
ffmpeg -hide_banner -y \
  -f lavfi -i "anullsrc=r=${SR}:cl=mono" \
  -c:a libmp3lame \
  -b:a "${BITRATE}" -minrate "${BITRATE}" -maxrate "${BITRATE}" -bufsize "${BITRATE}" \
  -ar "${SR}" -ac "${CHANNELS}" \
  -frames:a "${FRAMES}" \
  "${OUTPUT_FILE}"

echo
echo "Wrote: ${OUTPUT_FILE}"
echo

# =========================
# Probe duration
# =========================
echo "ffprobe container duration (seconds):"
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  "${OUTPUT_FILE}"

echo
echo "ffprobe audio stream duration (seconds):"
ffprobe -v error -select_streams a:0 -show_entries stream=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  "${OUTPUT_FILE}"

echo
echo "ffprobe stream details:"
ffprobe -v error -select_streams a:0 \
  -show_entries stream=codec_name,codec_long_name,profile,sample_rate,channels,channel_layout,bit_rate \
  -of default=noprint_wrappers=1 \
  "${OUTPUT_FILE}"
