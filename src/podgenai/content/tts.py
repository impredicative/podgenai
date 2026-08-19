import concurrent.futures

import pathvalidate

from podgenai.config import MAX_CONCURRENT_WORKERS
from podgenai.types import SpeechTask
from podgenai.util.binascii import hasher
from podgenai.util.openai import MODELS, ensure_speech_audio
from podgenai.util.semantic_text_splitter import semantic_split_by_length, semantic_split_by_tokens
from podgenai.util.tiktoken import get_token_count
from podgenai.work import get_topic_work_path


def get_speech_tasks(subtopics_speech_texts: dict[str, str], *, topic: str, voice: str) -> list[SpeechTask]:
    """Return the list of speech tasks, each containing the text and path to write as audio."""
    work_path = get_topic_work_path(topic)
    speech_tasks = []
    for part_num, (part_title, part) in enumerate(subtopics_speech_texts.items(), start=1):
        assert part_title.startswith(f"{part_num}. ")
        part_dedup_hash = hasher(part)
        part_stem = f"{part_title} ({MODELS['tts']}) ({voice}) [{part_dedup_hash}]"
        part_stem = pathvalidate.sanitize_filename(part_stem, platform="auto")
        match MODELS["tts"]:
            case "tts-1":
                max_tts_input_char_len = 4096
                if len(part) <= max_tts_input_char_len:
                    part_path = work_path / f"{part_stem}.mp3"
                    pathvalidate.validate_filepath(part_path, platform="auto")
                    speech_task = SpeechTask(path=part_path, text=part, portion_num=1, num_portions=1)
                    speech_tasks.append(speech_task)
                else:
                    portions = semantic_split_by_length(part, max_tts_input_char_len)
                    for portion_num, portion in enumerate(portions, start=1):
                        assert len(portion) <= max_tts_input_char_len
                        portion_path = work_path / f"{part_stem} ({portion_num}).mp3"
                        pathvalidate.validate_filepath(portion_path, platform="auto")
                        speech_task = SpeechTask(path=portion_path, text=portion, portion_num=portion_num, num_portions=len(portions))
                        speech_tasks.append(speech_task)
            case "gpt-4o-mini-tts-2025-12-15":
                max_tts_input_token_len = 2000
                overuse_mitigation_len = 100
                max_tts_input_token_len -= overuse_mitigation_len
                # Note: Overuse mitigation is performed to address an observed error such as the following:
                # openai.BadRequestError: Error code: 400 - {'error': {'message': 'Input of 2009 tokens is over the maximum input limit of 2000 tokens. Please shorten your input.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_value'}}
                # Whether this overuse is due to the TTS "instructions" using up tokens, or for a different reason, is not determined.
                if get_token_count(part, model=MODELS["tts"]) <= max_tts_input_token_len:
                    part_path = work_path / f"{part_stem}.mp3"
                    pathvalidate.validate_filepath(part_path, platform="auto")
                    speech_task = SpeechTask(path=part_path, text=part, portion_num=1, num_portions=1)
                    speech_tasks.append(speech_task)
                else:
                    portions = semantic_split_by_tokens(part, model=MODELS["tts"], limit=max_tts_input_token_len)
                    for portion_num, portion in enumerate(portions, start=1):
                        assert get_token_count(portion, model=MODELS["tts"]) <= max_tts_input_token_len
                        portion_path = work_path / f"{part_stem} ({portion_num}).mp3"
                        pathvalidate.validate_filepath(portion_path, platform="auto")
                        speech_task = SpeechTask(path=portion_path, text=portion, portion_num=portion_num, num_portions=len(portions))
                        speech_tasks.append(speech_task)
            case _:
                assert False
    return speech_tasks


def ensure_speech_audio_files(speech_tasks: list[SpeechTask], voice: str) -> None:
    """Ensure the speech audio files for the given speech tasks.

    If a given file path already exists, it is not rewritten. If it does not exist, it is written.
    """
    if MAX_CONCURRENT_WORKERS == 1:
        for speech_task in speech_tasks:
            ensure_speech_audio(speech_task["text"], path=speech_task["path"], voice=voice)
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_ensure_speech_audio = lambda speech_task: ensure_speech_audio(speech_task["text"], path=speech_task["path"], voice=voice)
            list(executor.map(fn_ensure_speech_audio, speech_tasks))
