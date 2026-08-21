import datetime
import functools
import json
import subprocess
from pathlib import Path
from typing import TypedDict

import pathvalidate

from podgenai.config import AUDIO_PATHS, CWD
from podgenai.types import SpeechTask
from podgenai.work import get_topic_work_path


class AudioFileMetadataForConcat(TypedDict):
    codec_name: str
    codec_type: str
    sample_rate: str
    channels: int
    channel_layout: str
    time_base: str


_EXPECTED_AUDIO_FILE_METADATA_FOR_CONCAT: AudioFileMetadataForConcat = {
    "codec_name": "mp3",
    "codec_type": "audio",
    "sample_rate": "24000",
    "channels": 1,
    "channel_layout": "mono",
    "time_base": "1/14112000",
}


@functools.lru_cache(maxsize=128)
def get_audio_file_metadata_for_concat(path: Path) -> AudioFileMetadataForConcat:
    """Return audio metadata relevant to stream-copy concatenation compatibility."""
    assert path.is_file()
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,codec_type,sample_rate,channels,channel_layout,time_base",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    streams = data.get("streams")
    assert streams and len(streams) == 1
    stream = streams[0]
    metadata = AudioFileMetadataForConcat(**stream)
    return metadata


def get_default_output_filename(topic: str) -> str:
    """Return the default output filename for the given topic."""
    now = datetime.datetime.now().isoformat(timespec="seconds")
    output_filename = f"{now} {topic}.mp3"
    output_filename = pathvalidate.sanitize_filename(output_filename, platform="auto")
    return output_filename


def get_output_file_path(output_path: Path | None, *, topic: str) -> Path:
    """Return the validated output file path for the given topic."""
    if output_path is None:
        output_filename = get_default_output_filename(topic)
        output_path = CWD / output_filename
    else:
        output_path = output_path.expanduser().resolve()
        if output_path.is_dir():
            assert output_path.exists()
            output_filename = get_default_output_filename(topic)
            output_path = output_path / output_filename
        else:
            assert output_path.suffix == ".mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)
    pathvalidate.validate_filepath(output_path, platform="auto")
    return output_path


def merge_speech_paths(speech_tasks: list[SpeechTask], *, topic: str, output_path: Path) -> None:
    """Merge the ordered list of preexisting audio file paths for the given topic to a single audio file having the given output file path."""

    short_pause_path, long_pause_path = AUDIO_PATHS["pause-0.25s"], AUDIO_PATHS["pause-0.50s"]
    assert _EXPECTED_AUDIO_FILE_METADATA_FOR_CONCAT == get_audio_file_metadata_for_concat(short_pause_path)
    assert _EXPECTED_AUDIO_FILE_METADATA_FOR_CONCAT == get_audio_file_metadata_for_concat(long_pause_path)

    paths = []
    for speech_task in speech_tasks:
        path = speech_task["path"]
        assert _EXPECTED_AUDIO_FILE_METADATA_FOR_CONCAT == get_audio_file_metadata_for_concat(path)
        if speech_task["portion_num"] < speech_task["num_portions"]:
            pause_path = short_pause_path
        elif (speech_task["portion_num"] == speech_task["num_portions"]) and (speech_task != speech_tasks[-1]):
            pause_path = long_pause_path
        else:
            pause_path = None
        paths.append(path)
        if pause_path is not None:
            paths.append(pause_path)

    work_path = get_topic_work_path(topic)
    ffmpeg_paths = [str(p).replace("'", "'\\''") for p in paths]
    ffmpeg_filelist_path = work_path / "ffmpeg.list"
    ffmpeg_filelist_path.write_text("\n".join(f"file '{p}'" for p in ffmpeg_paths))
    print(f"Merging {len(paths)} speech parts with pauses.")
    subprocess.run(["ffmpeg", "-y", "-xerror", "-f", "concat", "-safe", "0", "-i", str(ffmpeg_filelist_path), "-c", "copy", "-loglevel", "error", str(output_path)], check=True)
    assert output_path.exists()
    print(f"Merged {len(paths)} speech parts with pauses.")
