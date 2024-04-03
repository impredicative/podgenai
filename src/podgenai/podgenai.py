import concurrent.futures
import datetime
from pathlib import Path
import subprocess
from typing import Optional

import pathvalidate

from podgenai.config import MAX_CONCURRENT_WORKERS, PROMPTS, REPO_PATH, WORK_PATH
from podgenai.content.subtopics import list_subtopics, get_subtopic
from podgenai.content.topic import is_topic_valid
from podgenai.content.voice import get_voice
from podgenai.util.binascii import crc32 as hasher
from podgenai.util.openai import is_openai_key_available, TTS_VOICE_MAP, write_speech
from podgenai.util.str import split_text_by_paragraphs_and_limit


def _get_default_output_filename(topic: str) -> str:
    """Return the default output filename for the given topic."""
    now = datetime.datetime.now().isoformat(timespec='seconds')
    output_filename = f'{now} {topic}.mp3'
    output_filename = pathvalidate.sanitize_filename(output_filename, platform='auto')
    return output_filename


def generate_media(topic: str, *, output_path: Optional[Path] = None) -> Optional[Path]:
    """Return the output path after generating and writing an audiobook podcast to file for the given topic.

    Params:
    * `topic`: Topic.
    * `path`: Output file or directory path.
        If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined.
        If not given, the output file is written to the repo directory with an auto-determined file name.

    If successful, the output path is returned. If failed for a common reason, `None` is returned, and a relevant error is printed.
    As such, the return value must be checked.
    """
    assert is_openai_key_available()
    assert is_topic_valid(topic)
    print(f'TOPIC: {topic}')

    voice = get_voice(topic)
    mapped_voice = TTS_VOICE_MAP[voice]
    print(f'VOICE: {voice} ({mapped_voice})')

    subtopics_list = list_subtopics(topic)  # Already validated.
    if not subtopics_list:
        return
    print(f'\nSUBTOPICS:\n{'\n'.join(subtopics_list)}')
    print(f'\nWORKERS: {MAX_CONCURRENT_WORKERS}')
    if MAX_CONCURRENT_WORKERS == 1:
        subtopics = {s: get_subtopic(topic=topic, subtopics=subtopics_list, subtopic=s) for s in subtopics_list}
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_get_subtopic = lambda subtopic: get_subtopic(topic=topic, subtopics=subtopics_list, subtopic=subtopic)
            subtopics = {s: text for s, text in zip(subtopics_list, executor.map(fn_get_subtopic, subtopics_list))}

    parts = [f'Section {subtopic_name.replace('.', ':', 1)}:\n\n{subtopic_text} {{pause}}' for subtopic_name, subtopic_text in subtopics.items()]
    # Note: A pause at the beginning is skipped by the TTS generator, but it is not skipped if at the end, and so it is kept at the end.
    parts[0] = f'"{topic}"\n\n{{pause}}\n{PROMPTS['tts_disclaimer']} {{pause}}\n\n{parts[0]}'
    # Note: TTS disclaimer about AI generated audio is required by OpenAI as per https://platform.openai.com/docs/guides/text-to-speech/do-i-own-the-outputted-audio-files
    # Note: It has proven more reliable for the pause to be structured in this way for section 1, rather than be in the leading topic line.
    text = '\n\n'.join(parts)
    print(f'\nTEXT:\n{text}')

    if output_path is None:
        output_filename = _get_default_output_filename(topic)
        output_path = REPO_PATH / output_filename
    else:
        output_path = output_path.expanduser().resolve()
        if output_path.is_dir():
            assert output_path.exists()
            output_filename = _get_default_output_filename(topic)
            output_path = output_path / output_filename
        else:
            assert output_path.suffix == '.mp3'
            output_path.parent.mkdir(parents=True, exist_ok=True)

    pathvalidate.validate_filepath(output_path, platform='auto')

    max_tts_input_len = 4096
    work_path = WORK_PATH / pathvalidate.sanitize_filepath(topic, platform='auto')
    pathvalidate.validate_filepath(work_path, platform='auto')
    tts_tasks = []
    for part_idx, part in enumerate(parts):
        part_title = subtopics_list[part_idx]
        part_dedup_hash = hasher(part)
        part_stem = f'{part_title} ({mapped_voice}) [{part_dedup_hash}]'
        part_stem = pathvalidate.sanitize_filename(part_stem, platform='auto')
        if len(part) <= max_tts_input_len:
            part_path = work_path / f'{part_stem}.mp3'
            pathvalidate.validate_filepath(part_path, platform='auto')
            tts_tasks.append({'path': part_path, 'text': part})
        else:
            portions = split_text_by_paragraphs_and_limit(part, max_tts_input_len)
            for portion_num, portion in enumerate(portions, start=1):
                assert len(portion) <= max_tts_input_len
                portion_path = work_path / f'{part_stem} ({portion_num}).mp3'
                pathvalidate.validate_filepath(portion_path, platform='auto')
                tts_tasks.append({'path': portion_path, 'text': portion})
    work_path.mkdir(parents=False, exist_ok=True)
    tts_tasks_pending = [t for t in tts_tasks if not t['path'].exists()]
    if MAX_CONCURRENT_WORKERS == 1:
        for tts_task in tts_tasks_pending:
            write_speech(tts_task['text'], path=tts_task['path'], voice=voice)
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_write_speech = lambda tts_task: write_speech(tts_task['text'], path=tts_task['path'], voice=voice)
            list(executor.map(fn_write_speech, tts_tasks_pending))

    part_paths = [t['path'] for t in tts_tasks]
    ffmpeg_paths = [str(p).replace("'", "'\\''") for p in part_paths]
    ffmpeg_filelist_path = work_path / 'mp3.list'
    ffmpeg_filelist_path.write_text('\n'.join(f"file '{p}'" for p in ffmpeg_paths))
    print(f'\nMerging {len(part_paths)} parts to: {output_path}')
    subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(ffmpeg_filelist_path), '-c', 'copy', str(output_path)], check=True)
    assert output_path.exists()
    print(f'Finished merging {len(part_paths)} parts to: {output_path}')

    return output_path
