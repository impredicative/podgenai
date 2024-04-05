import concurrent.futures
from pathlib import Path

from podgenai.config import MAX_CONCURRENT_WORKERS, PROMPTS
from podgenai.util.openai import ensure_speech


def get_text_parts(subtopics: dict[str, str], *, topic: str) -> list[str]:
    """Return an ordered list of texts for TTS inputs for the given ordered subtopics and topic.

    One text is returned for each subtopic.
    """
    parts = [f'Section {subtopic_name.replace('.', ':', 1)}:\n\n{subtopic_text} {{pause}}' for subtopic_name, subtopic_text in subtopics.items()]
    # Note: A pause at the beginning is skipped by the TTS generator, but it is not skipped if at the end, and so it is kept at the end.
    parts[0] = f'"{topic}"\n\n{{pause}}\n{PROMPTS['tts_disclaimer']} {{pause}}\n\n{parts[0]}'
    # Note: TTS disclaimer about AI generated audio is required by OpenAI as per https://platform.openai.com/docs/guides/text-to-speech/do-i-own-the-outputted-audio-files
    # Note: It has proven more reliable for the pause to be structured in this way for section 1, rather than be in the leading topic line.
    return parts


def ensure_speech_parts(parts: dict[Path, str], voice: str) -> None:
    """Ensure the speech files for the given part file path and text pairs.

    If a given file path already exists, it is not rewritten. If it does not exist, it is written.
    """
    if MAX_CONCURRENT_WORKERS == 1:
        for part_path, part_text in parts.items():
            ensure_speech(part_text, path=part_path, voice=voice)
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_ensure_speech = lambda part_path: ensure_speech(parts[part_path], path=part_path, voice=voice)
            list(executor.map(fn_ensure_speech, parts))
