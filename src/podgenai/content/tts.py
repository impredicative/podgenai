import concurrent.futures

import pathvalidate

from podgenai.config import MAX_CONCURRENT_WORKERS, MAX_TEXT_LENGTH_IN_FILENAME, PAUSE_BETWEEN_PARTS, PAUSE_BETWEEN_SUBTOPICS, PROMPTS
from podgenai.types import SpeechTask, SubtopicDuologue, SubtopicText
from podgenai.util.binascii import hasher
from podgenai.util.openai import MODELS, TTS_VOICE_MAP, ensure_speech_audio
from podgenai.util.semantic_text_splitter import semantic_split_by_length, semantic_split_by_tokens
from podgenai.util.tiktoken import get_token_count
from podgenai.work import get_topic_work_path


def get_monologue_pause(*, part_num: int, num_parts: int, subtopic_num: int, num_subtopics: int) -> float | None:
    """Return the pause after a given part of a subtopic."""
    is_last_part_of_subtopic = part_num == num_parts
    is_last_subtopic = subtopic_num == num_subtopics
    if not is_last_part_of_subtopic:
        return PAUSE_BETWEEN_PARTS
    if is_last_part_of_subtopic and not is_last_subtopic:
        return PAUSE_BETWEEN_SUBTOPICS
    return None


def get_duologue_pause(*, line_num: int, num_lines: int, part_num: int, num_parts: int, subtopic_num: int, num_subtopics: int) -> float | None:
    """Return the pause after a given part of a line of a subtopic."""
    is_last_part_of_line = part_num == num_parts
    is_last_line_of_subtopic = line_num == num_lines
    is_last_subtopic = subtopic_num == num_subtopics
    if not (is_last_part_of_line and is_last_line_of_subtopic):
        return PAUSE_BETWEEN_PARTS
    if is_last_part_of_line and is_last_line_of_subtopic and not is_last_subtopic:
        return PAUSE_BETWEEN_SUBTOPICS
    return None


def get_monologue_speech_tasks(*, subtopics_monologue_transcripts: list[SubtopicText], topic: str, voice_key: str) -> list[SpeechTask]:
    """Return the list of speech tasks for the monologue."""
    work_path = get_topic_work_path(topic)
    voice = TTS_VOICE_MAP[voice_key]
    tts_model = MODELS["tts"]
    assert subtopics_monologue_transcripts
    num_subtopics = len(subtopics_monologue_transcripts)

    speech_tasks = []
    for subtopic_num, subtopic in enumerate(subtopics_monologue_transcripts, start=1):
        subtopic_title = subtopic["name"]
        subtopic_monologue = subtopic["text"]
        assert subtopic_title.startswith(f"{subtopic_num}. ")
        match tts_model:
            case "tts-1":
                # Note: Support of this older TTS model in this application is eventually meant to be cleanly removed.
                subtopic_dedup_hash = hasher(subtopic_monologue)
                filename_stem = f"{subtopic_title[:MAX_TEXT_LENGTH_IN_FILENAME]} (monologue) ({tts_model}) ({voice}) [{subtopic_dedup_hash}]"
                filename_stem = pathvalidate.sanitize_filename(filename_stem, platform="auto")
                max_tts_input_char_len = 4096
                if len(subtopic_monologue) <= max_tts_input_char_len:
                    filename_path = work_path / f"{filename_stem}.mp3"
                    pathvalidate.validate_filepath(filename_path, platform="auto")
                    pause_after = get_monologue_pause(part_num=1, num_parts=1, subtopic_num=subtopic_num, num_subtopics=num_subtopics)
                    speech_task = SpeechTask(path=filename_path, text=subtopic_monologue, part_num=1, num_parts=1, voice=voice, tone=None, pause_after=pause_after)  # Note: Tone instructions are not supported by this TTS model.
                    speech_tasks.append(speech_task)
                else:
                    parts = semantic_split_by_length(subtopic_monologue, max_tts_input_char_len)
                    num_parts = len(parts)
                    for part_num, part in enumerate(parts, start=1):
                        assert len(part) <= max_tts_input_char_len
                        part_path = work_path / f"{filename_stem} ({part_num}\N{DIVISION SLASH}{num_parts}).mp3"
                        pathvalidate.validate_filepath(part_path, platform="auto")
                        pause_after = get_monologue_pause(part_num=part_num, num_parts=num_parts, subtopic_num=subtopic_num, num_subtopics=num_subtopics)
                        speech_task = SpeechTask(path=part_path, text=part, part_num=part_num, num_parts=num_parts, voice=voice, tone=None, pause_after=pause_after)  # Note: Tone instructions are not supported by this TTS model.
                        speech_tasks.append(speech_task)
            case "gpt-4o-mini-tts-2025-12-15":
                tone_instructions = PROMPTS["tts_monologue_tone"]
                subtopic_dedup_hash = hasher(f"{subtopic_monologue}\n\n{tone_instructions}")
                filename_stem = f"{subtopic_title[:MAX_TEXT_LENGTH_IN_FILENAME]} (monologue) ({tts_model}) ({voice}) [{subtopic_dedup_hash}]"
                filename_stem = pathvalidate.sanitize_filename(filename_stem, platform="auto")
                max_tts_input_token_len = 2000
                overuse_mitigation_len = 100
                max_tts_input_token_len -= overuse_mitigation_len
                # Note: Overuse mitigation is performed to address an observed error such as the following:
                # openai.BadRequestError: Error code: 400 - {'error': {'message': 'Input of 2009 tokens is over the maximum input limit of 2000 tokens. Please shorten your input.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_value'}}
                # Whether this overuse is due to the TTS "instructions" using up tokens, or for a different reason, is not determined. Fwiw, the TTS monologue instructions were observed to use 36 tokens.
                if get_token_count(subtopic_monologue, model=tts_model) <= max_tts_input_token_len:
                    part_path = work_path / f"{filename_stem}.mp3"
                    pathvalidate.validate_filepath(part_path, platform="auto")
                    pause_after = get_monologue_pause(part_num=1, num_parts=1, subtopic_num=subtopic_num, num_subtopics=num_subtopics)
                    speech_task = SpeechTask(path=part_path, text=subtopic_monologue, part_num=1, num_parts=1, voice=voice, tone=tone_instructions, pause_after=pause_after)
                    speech_tasks.append(speech_task)
                else:
                    parts = semantic_split_by_tokens(subtopic_monologue, model=tts_model, limit=max_tts_input_token_len)
                    num_parts = len(parts)
                    for part_num, part in enumerate(parts, start=1):
                        assert get_token_count(part, model=tts_model) <= max_tts_input_token_len
                        part_path = work_path / f"{filename_stem} ({part_num}\N{DIVISION SLASH}{num_parts}).mp3"
                        pathvalidate.validate_filepath(part_path, platform="auto")
                        pause_after = get_monologue_pause(part_num=part_num, num_parts=num_parts, subtopic_num=subtopic_num, num_subtopics=num_subtopics)
                        speech_task = SpeechTask(path=part_path, text=part, part_num=part_num, num_parts=num_parts, voice=voice, tone=tone_instructions, pause_after=pause_after)
                        speech_tasks.append(speech_task)
            case _:
                assert False
    return speech_tasks


def get_duologue_speech_tasks(*, subtopics_duologues: list[SubtopicDuologue], topic: str, male_voice_key: str, female_voice_key: str) -> list[SpeechTask]:
    """Return the list of speech tasks for the duologue."""
    work_path = get_topic_work_path(topic)
    tts_model = MODELS["tts"]
    voices = {"male": TTS_VOICE_MAP[male_voice_key], "female": TTS_VOICE_MAP[female_voice_key]}
    assert subtopics_duologues
    num_subtopics = len(subtopics_duologues)

    speech_tasks = []
    for subtopic_num, subtopic_duologue in enumerate(subtopics_duologues, start=1):
        subtopic_title = subtopic_duologue["subtopic"]
        subtopic_path = f"{subtopic_title[:MAX_TEXT_LENGTH_IN_FILENAME]} (duologue) ({tts_model})"
        subtopic_path = pathvalidate.sanitize_filename(subtopic_path, platform="auto")
        duologue = subtopic_duologue["duologue"]
        assert subtopic_title.startswith(f"{subtopic_num}. ")
        assert duologue

        num_lines = len(duologue)
        for line_num, line in enumerate(duologue, start=1):
            line_id = f"S{subtopic_num}L{line_num - 1}"  # Note: subtopic_num is included here for convenience in subsequent logging. line_id starts at 0, as the first line is the section marker.
            speaker = line["speaker"]
            assert speaker in ("male", "female")
            voice = voices[speaker]
            speech = line["speech"]
            tone = line["tone"]
            filename_speech = speech.replace("\n", " ")[:MAX_TEXT_LENGTH_IN_FILENAME]
            line_dedup_hash = hasher(f"{speech}\n\n{tone or ''}")
            filename_stem = f"{line_id}. {filename_speech} ({voice}) [{line_dedup_hash}]"
            filename_stem = pathvalidate.sanitize_filename(filename_stem, platform="universal")  # Note: platform is "universal" to handle all variations of newlines that are possible in the speech text which is used in the filename stem.

            match tts_model:
                case "tts-1":
                    # Note: Support of this older TTS model in this application is eventually meant to be cleanly removed.
                    max_tts_input_char_len = 4096
                    parts = [speech] if len(speech) <= max_tts_input_char_len else semantic_split_by_length(speech, max_tts_input_char_len)
                    tone = None  # Tone instructions are not supported by this TTS model.
                case "gpt-4o-mini-tts-2025-12-15":
                    max_tts_input_token_len = 2000
                    overuse_mitigation_len = max(100, get_token_count(tone or "", model=tts_model))
                    max_tts_input_token_len -= overuse_mitigation_len
                    # Note: Overuse mitigation is performed to address an observed error such as the following:
                    # openai.BadRequestError: Error code: 400 - {'error': {'message': 'Input of 2009 tokens is over the maximum input limit of 2000 tokens. Please shorten your input.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_value'}}
                    # Whether this overuse is due to the TTS "instructions" using up tokens, or for a different reason, is not determined.
                    parts = [speech] if get_token_count(speech, model=tts_model) <= max_tts_input_token_len else semantic_split_by_tokens(speech, model=tts_model, limit=max_tts_input_token_len)
                case _:
                    assert False

            num_parts = len(parts)
            for part_num, part in enumerate(parts, start=1):
                match tts_model:
                    case "tts-1":
                        assert len(part) <= max_tts_input_char_len
                        assert tone is None
                    case "gpt-4o-mini-tts-2025-12-15":
                        assert get_token_count(part, model=tts_model) <= max_tts_input_token_len
                    case _:
                        assert False

                part_suffix = f" ({part_num}\N{DIVISION SLASH}{num_parts})" if num_parts > 1 else ""
                filename = f"{filename_stem}{part_suffix}.mp3"
                pathvalidate.validate_filename(filename, platform="auto")
                part_path = work_path / subtopic_path / filename
                pathvalidate.validate_filepath(part_path, platform="auto")
                pause_after = get_duologue_pause(line_num=line_num, num_lines=num_lines, part_num=part_num, num_parts=num_parts, subtopic_num=subtopic_num, num_subtopics=num_subtopics)
                speech_task = SpeechTask(path=part_path, text=part, part_num=part_num, num_parts=num_parts, voice=voice, tone=tone, pause_after=pause_after)
                speech_tasks.append(speech_task)

    return speech_tasks


def ensure_speech_audio_files(speech_tasks: list[SpeechTask]) -> None:
    """Ensure the speech audio files for the given speech tasks.

    If a given file path already exists, it is not rewritten. If it does not exist, it is written.
    """
    if MAX_CONCURRENT_WORKERS == 1:
        for speech_task in speech_tasks:
            ensure_speech_audio(text=speech_task["text"], path=speech_task["path"], voice=speech_task["voice"], tone=speech_task["tone"])
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_ensure_speech_audio = lambda speech_task: ensure_speech_audio(text=speech_task["text"], path=speech_task["path"], voice=speech_task["voice"], tone=speech_task["tone"])
            list(executor.map(fn_ensure_speech_audio, speech_tasks))
