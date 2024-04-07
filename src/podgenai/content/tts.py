import concurrent.futures
from pathlib import Path

import pathvalidate

from podgenai.config import MAX_CONCURRENT_WORKERS
from podgenai.util.binascii import hasher
from podgenai.util.openai import ensure_speech_audio, MAX_TTS_INPUT_LEN
from podgenai.util.semantic_text_splitter import semantic_split
from podgenai.work import get_topic_work_path


def get_speech_tasks(subtopics_speech_texts: dict[str, str], *, topic: str, voice: str) -> dict[Path, str]:
    """Return the pairs of texts to write to file paths as audio."""
    work_path = get_topic_work_path(topic)
    tts_tasks = {}
    for part_idx, (part_title, part) in enumerate(subtopics_speech_texts.items()):
        part_dedup_hash = hasher(part)
        part_stem = f"{part_title} ({voice}) [{part_dedup_hash}]"
        part_stem = pathvalidate.sanitize_filename(part_stem, platform="auto")
        if len(part) <= MAX_TTS_INPUT_LEN:
            part_path = work_path / f"{part_stem}.mp3"
            pathvalidate.validate_filepath(part_path, platform="auto")
            tts_tasks[part_path] = part
        else:
            portions = semantic_split(part, MAX_TTS_INPUT_LEN)
            for portion_num, portion in enumerate(portions, start=1):
                assert len(portion) <= MAX_TTS_INPUT_LEN
                portion_path = work_path / f"{part_stem} ({portion_num}).mp3"
                pathvalidate.validate_filepath(portion_path, platform="auto")
                tts_tasks[portion_path] = portion
    return tts_tasks


def ensure_speech_audio_files(parts: dict[Path, str], voice: str) -> None:
    """Ensure the speech audio files for the given part file path and text pairs.

    If a given file path already exists, it is not rewritten. If it does not exist, it is written.
    """
    if MAX_CONCURRENT_WORKERS == 1:
        for part_path, part_text in parts.items():
            ensure_speech_audio(part_text, path=part_path, voice=voice)
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_ensure_speech_audio = lambda part_path: ensure_speech_audio(parts[part_path], path=part_path, voice=voice)
            list(executor.map(fn_ensure_speech_audio, parts))
