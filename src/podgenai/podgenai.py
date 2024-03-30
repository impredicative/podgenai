import datetime
from pathlib import Path
from typing import Optional

from podgenai.config import REPO_PATH
from podgenai.subtopics import list_subtopics, get_subtopic
from podgenai.topic import is_topic_valid
from podgenai.util.openai import is_openai_key_available, TTS_DISCLAIMER, write_speech


def generate_podcast(topic: str, *, output_path: Optional[Path] = None) -> Path:
    """Return the output path after generating and writing a podcast to file for the given topic."""
    assert is_openai_key_available()
    assert is_topic_valid(topic)
    print(f'\nTOPIC: {topic}')

    subtopics_list = list_subtopics(topic)  # Already validated.
    print(f'\nSUBTOPICS:\n{'\n'.join(subtopics_list)}')
    subtopics = {s: get_subtopic(topic=topic, subtopics=subtopics_list, subtopic=s) for s in subtopics_list}
    subtopics = [f'{{pause}} Section {subtopic_name.replace('.', ':', 1)}:\n{subtopic_text}' for subtopic_name, subtopic_text in subtopics.items()]

    parts = subtopics.copy()
    parts[0] = f'{topic}\n\n{parts[0]}'
    parts[-1] = f'{parts[-1]}\n\n{{pause}} {TTS_DISCLAIMER}'
    text = '\n\n'.join(parts)
    print(f'\nTEXT:\n{text}')

    if output_path is None:
        now = datetime.datetime.now().isoformat(timespec='seconds')
        output_path = REPO_PATH / f'{now} {topic}.mp3'

    for num, part in enumerate(parts):
        assert len(part) < 4096  # TODO: Split part across paragraphs if longer.
        part_path = output_path.with_name(f'{topic} - {subtopics_list[num]}.mp3')
        if not part_path.exists():  # TODO: Use proper disk cache instead.
            write_speech(part, part_path)

    return output_path
