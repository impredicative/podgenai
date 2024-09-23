from pathlib import Path
from typing import Optional

from podgenai.config import MAX_CONCURRENT_WORKERS, NUM_SECTIONS_MIN, NUM_SECTIONS_MAX
from podgenai.content.audio import get_output_file_path, merge_speech_paths
from podgenai.content.subtopics import list_subtopics, get_subtopics_speech_texts
from podgenai.content.topic import ensure_topic_is_valid
from podgenai.content.tts import get_speech_tasks, ensure_speech_audio_files
from podgenai.content.voice import get_voice
from podgenai.exceptions import InputError
from podgenai.util.input import get_confirmation
from podgenai.util.openai import ensure_openai_key, MODELS, TTS_VOICE_MAP
from podgenai.work import get_topic_work_path


def generate_media(topic: str, *, output_path: Optional[Path] = None, max_sections: Optional[int] = None, markers: bool = True, confirm: bool = False) -> Path:
    """Return the output path after generating and writing an audiobook podcast to file for the given topic.

    Params:
    * `topic`: Topic.
    * `path`: Output file or directory path.
        If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined.
        If not given, the output file is written to the repo directory with an auto-determined file name.
    * `max_sections`: Maximum number of sections to generate. It is between 3 and 100. It is unrestricted if not given.
    * `markers`: Include markers at the start or end of sections in the generated audio.
        If true, markers are included. If false, markers are excluded, as can be appropriate for foreign-language generation. Its default is true.
    * `confirm`: Confirm before full-text and speech generation.
        If true, a confirmation is interactively sought after generating and printing the list of subtopics, before generating the full-text, and also before generating the speech. Its default is false.

    If failed, a subclass of the `podgenai.exceptions.Error` exception is raised.
    """
    ensure_openai_key()
    ensure_topic_is_valid(topic)
    print(f"TOPIC: {topic}")

    work_path = get_topic_work_path(topic)
    print(f"CACHE: {work_path}")
    print(f"MODELS: text={MODELS["text"]}, tts={MODELS["tts"]}")
    print(f"WORKERS: {MAX_CONCURRENT_WORKERS}")
    if max_sections is not None:
        if not (NUM_SECTIONS_MIN <= max_sections <= NUM_SECTIONS_MAX):
            raise InputError(f"Max sections is {max_sections} but it must be between {NUM_SECTIONS_MIN} and {NUM_SECTIONS_MAX}.")
        print(f"SECTIONS: ≤{max_sections}")
    print(f"MARKERS: {'enabled' if markers else 'disabled'}")

    subtopics_list = list_subtopics(topic, max_sections=max_sections)  # Can commonly raise an exception, so it's done before getting voice.

    voice = get_voice(topic)
    mapped_voice = TTS_VOICE_MAP[voice]
    print(f"VOICE: {voice} ({mapped_voice})")
    print(f'SUBTOPICS:\n{'\n'.join(subtopics_list)}')

    if confirm:
        get_confirmation("text generation")
    subtopics_speech_texts = get_subtopics_speech_texts(topic=topic, subtopics=subtopics_list, markers=markers)
    assert subtopics_speech_texts
    speech_text = "\n\n".join(subtopics_speech_texts.values())
    print(f"\nSPEECH:\n{speech_text}\n")

    if confirm:
        get_confirmation("speech generation")
    speech_tasks = get_speech_tasks(subtopics_speech_texts, topic=topic, voice=mapped_voice)
    ensure_speech_audio_files(speech_tasks, voice=voice)

    speech_paths = list(speech_tasks)
    output_path = get_output_file_path(output_path, topic=topic)
    merge_speech_paths(speech_paths, topic=topic, output_path=output_path)
    print(f"OUTPUT: {output_path}")
    return output_path
