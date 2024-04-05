from pathlib import Path
from typing import Optional

from podgenai.config import MAX_CONCURRENT_WORKERS
from podgenai.content.audio import get_output_file_path, merge_speech_paths
from podgenai.content.subtopics import list_subtopics, get_subtopics_speech_texts
from podgenai.content.topic import is_topic_valid
from podgenai.content.tts import get_speech_tasks, ensure_speech_audio_files
from podgenai.content.voice import get_voice
from podgenai.util.openai import is_openai_key_available, TTS_VOICE_MAP
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

    subtopics_speech_texts = get_subtopics_speech_texts(topic=topic, subtopics=subtopics_list)
    assert subtopics_speech_texts
    speech_text = "\n\n".join(subtopics_speech_texts.values())
    print(f"\nSPEECH:\n{speech_text}\n")

    speech_tasks = get_speech_tasks(subtopics_speech_texts, topic=topic, voice=mapped_voice)
    ensure_speech_audio_files(speech_tasks, voice=voice)

    speech_paths = list(speech_tasks)
    output_path = get_output_file_path(output_path, topic=topic)
    merge_speech_paths(speech_paths, topic=topic, output_path=output_path)
    print(f"OUTPUT: {output_path}")
    return output_path
