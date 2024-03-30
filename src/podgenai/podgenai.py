import datetime
from pathlib import Path
import subprocess
from typing import Optional

from podgenai.config import REPO_PATH, WORK_PATH
from podgenai.subtopics import list_subtopics, get_subtopic
from podgenai.topic import is_topic_valid
from podgenai.util.openai import is_openai_key_available, TTS_DISCLAIMER, write_speech
from podgenai.util.str import split_text_by_paragraphs_and_limit
from podgenai.util.sys import print_error


def generate_podcast(topic: str, *, output_path: Optional[Path] = None) -> Optional[Path]:
    """Return the output path after generating and writing a podcast to file for the given topic.

    No path is returned if the podcast fails to be generated.
    """
    assert is_openai_key_available()
    assert is_topic_valid(topic)
    print(f'\nTOPIC: {topic}')

    subtopics_list = list_subtopics(topic)  # Already validated.
    if not subtopics_list:
        print_error(f'Failed to generate podcast for topic: {topic}')
        return
    print(f'\nSUBTOPICS:\n{'\n'.join(subtopics_list)}')
    subtopics = {s: get_subtopic(topic=topic, subtopics=subtopics_list, subtopic=s) for s in subtopics_list}
    subtopics = [f'Section {subtopic_name.replace('.', ':', 1)}:\n{subtopic_text} {{pause}}' for subtopic_name, subtopic_text in subtopics.items()]
    # Note: A pause at the beginning is skipped by the TTS generator, but it is not skipped if at the end, and so it is kept at the end.

    parts = subtopics.copy()
    parts[0] = f'{topic}\n\n{{pause}}\n{parts[0]}'  # Note: It has proven more reliable for the pause to be structured in this way for section 1, rather than be in the leading line.
    parts[-1] = f'{parts[-1]}\n\n {TTS_DISCLAIMER}'
    text = '\n\n'.join(parts)
    print(f'\nTEXT:\n{text}')

    if output_path is None:
        now = datetime.datetime.now().isoformat(timespec='seconds')
        output_path = REPO_PATH / f'{now} {topic}.mp3'

    part_paths = []
    max_tts_input_len = 4096
    work_path = WORK_PATH / topic
    work_path.mkdir(parents=False, exist_ok=True)
    for part_idx, part in enumerate(parts):
        if len(part) <= max_tts_input_len:
            part_path = work_path / f'{subtopics_list[part_idx]}.mp3'
            part_paths.append(part_path)
            if not part_path.exists():  # TODO: Use proper disk cache instead.
                write_speech(part, part_path)
        else:
            portions = split_text_by_paragraphs_and_limit(part, max_tts_input_len)
            for portion_num, portion in enumerate(portions, start=1):
                assert len(portion) <= max_tts_input_len
                portion_path = work_path / f'{subtopics_list[part_idx]} ({portion_num}).mp3'
                part_paths.append(portion_path)
                if not portion_path.exists():  # TODO: Use proper disk cache instead.
                    write_speech(portion, portion_path)

    ffmpeg_filelist_path = work_path / 'mp3.list'
    ffmpeg_filelist_path.write_text('\n'.join(f"file '{str(p).replace("'", "'\\''")}'" for p in part_paths))
    print(f'\nMerging {len(part_paths)} parts to: {output_path}')
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(ffmpeg_filelist_path), '-c', 'copy', str(output_path)], check=True)
    print(f'Finished merging {len(part_paths)} parts to: {output_path}')

    return output_path
