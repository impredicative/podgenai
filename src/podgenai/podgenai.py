from pathlib import Path
from typing import Optional

import pathvalidate

from podgenai.config import MAX_CONCURRENT_WORKERS
from podgenai.content.audio import get_output_file_path, merge_speech_parts
from podgenai.content.subtopics import list_subtopics, get_subtopics
from podgenai.content.topic import is_topic_valid
from podgenai.content.tts import get_text_parts, ensure_speech_parts
from podgenai.content.voice import get_voice
from podgenai.util.binascii import crc32 as hasher
from podgenai.util.openai import is_openai_key_available, TTS_VOICE_MAP, write_speech
from podgenai.util.str import split_text_by_paragraphs_and_limit
from podgenai.util.sys import print_warning
from podgenai.work import get_topic_work_path


def generate_media(topic: str, *, output_path: Optional[Path] = None, confirm: bool = False) -> Optional[Path]:
    """Return the output path after generating and writing an audiobook podcast to file for the given topic.

    Params:
    * `topic`: Topic.
    * `path`: Output file or directory path.
        If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined.
        If not given, the output file is written to the repo directory with an auto-determined file name.
    * `confirm`: Confirm before full-text generation.
        If true, a confirmation is interactively sought after generating and printing the list of subtopics, before generating the full-text. Its default is false.

    If successful, the output path is returned. If failed for a common reason, `None` is returned, and a relevant error is printed.
    As such, the return value must be checked.
    """
    assert is_openai_key_available()
    assert is_topic_valid(topic)
    print(f"TOPIC: {topic}")

    work_path = get_topic_work_path(topic)
    print(f"CACHE: {work_path}")
    print(f"WORKERS: {MAX_CONCURRENT_WORKERS}")

    voice = get_voice(topic)
    mapped_voice = TTS_VOICE_MAP[voice]
    print(f"VOICE: {voice} ({mapped_voice})")

    subtopics_list = list_subtopics(topic)  # Already validated.
    if not subtopics_list:
        return
    print(f'SUBTOPICS:\n{'\n'.join(subtopics_list)}')

    if confirm:
        while True:
            response = input("Continue? [y/n]: ")
            response = response.strip().lower()
            match response:
                case "y" | "yes":
                    break
                case "n" | "no":
                    print_warning("User aborted.")
                    return

    assert subtopics_list
    subtopics = get_subtopics(topic=topic, subtopics=subtopics_list)
    assert subtopics
    text_parts = get_text_parts(subtopics, topic=topic)
    text = "\n\n".join(text_parts)
    print(f"\nTEXT:\n{text}\n")

    max_tts_input_len = 4096
    tts_tasks = []
    for part_idx, part in enumerate(text_parts):
        part_title = subtopics_list[part_idx]
        part_dedup_hash = hasher(part)
        part_stem = f"{part_title} ({mapped_voice}) [{part_dedup_hash}]"
        part_stem = pathvalidate.sanitize_filename(part_stem, platform="auto")
        if len(part) <= max_tts_input_len:
            part_path = work_path / f"{part_stem}.mp3"
            pathvalidate.validate_filepath(part_path, platform="auto")
            tts_tasks.append({"path": part_path, "text": part})
        else:
            portions = split_text_by_paragraphs_and_limit(part, max_tts_input_len)
            for portion_num, portion in enumerate(portions, start=1):
                assert len(portion) <= max_tts_input_len
                portion_path = work_path / f"{part_stem} ({portion_num}).mp3"
                pathvalidate.validate_filepath(portion_path, platform="auto")
                tts_tasks.append({"path": portion_path, "text": portion})

    tts_tasks = {t['path']: t['text'] for t in tts_tasks}
    ensure_speech_parts(tts_tasks, voice=voice)

    part_paths = list(tts_tasks)
    output_path = get_output_file_path(output_path, topic=topic)
    merge_speech_parts(part_paths, topic=topic, output_path=output_path)
    print(f"OUTPUT: {output_path}")
    return output_path
