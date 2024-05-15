import datetime
from pathlib import Path
import subprocess
from typing import Optional

import pathvalidate

from podgenai.config import CWD
from podgenai.work import get_topic_work_path


def get_default_output_filename(topic: str) -> str:
    """Return the default output filename for the given topic."""
    now = datetime.datetime.now().isoformat(timespec="seconds")
    output_filename = f"{now} {topic}.mp3"
    output_filename = pathvalidate.sanitize_filename(output_filename, platform="auto")
    return output_filename


def get_output_file_path(output_path: Optional[Path], *, topic: str) -> Path:
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


def merge_speech_paths(paths: list[Path], *, topic: str, output_path: Path) -> None:
    """Merge the ordered list of preexisting audio file paths for the given topic to a single audio file having the given output file path."""
    work_path = get_topic_work_path(topic)
    ffmpeg_paths = [str(p).replace("'", "'\\''") for p in paths]
    ffmpeg_filelist_path = work_path / "ffmpeg.list"
    ffmpeg_filelist_path.write_text("\n".join(f"file '{p}'" for p in ffmpeg_paths))
    print(f"Merging {len(paths)} speech parts.")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(ffmpeg_filelist_path), "-c", "copy", "-loglevel", "error", str(output_path)], check=True)
    assert output_path.exists()
    print(f"Merged {len(paths)} speech parts.")
