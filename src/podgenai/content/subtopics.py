import concurrent.futures
import contextlib
import io
from typing import Optional

import podgenai.exceptions
from podgenai.config import MAX_CONCURRENT_WORKERS, PROMPTS, NUM_SECTIONS_MIN, NUM_SECTIONS_MAX
from podgenai.util.openai import get_cached_content
from podgenai.work import get_topic_work_path
from podgenai.util.sys import print_error, print_warning


def is_subtopics_list_valid(subtopics: list[str], max_sections: Optional[int]) -> bool:
    """Return true if the subtopics are structurally valid, otherwise false.

    A validation error is printed if a subtopic is invalid.
    """
    if not subtopics:
        print_error("No subtopics exist.")
        return False

    if max_sections is not None:
        if len(subtopics) > max_sections:
            print_error(f"Up to {max_sections} subtopics are allowed, but {len(subtopics)} exist.")
            return False

    seen = set()
    for num, subtopic in enumerate(subtopics, start=1):
        if subtopic != subtopic.strip():
            print_error(f"Subtopic {num} is invalid because it has leading or trailing whitespace: {subtopic!r}")
            return False

        expected_num_prefix = f"{num}. "
        if not subtopic.startswith(expected_num_prefix):
            print_error(f"Subtopic {num} is invalid because it is not numbered correctly: {subtopic}")
            return False

        subtopic_name = subtopic.removeprefix(expected_num_prefix).strip()
        if not subtopic_name:
            print_error(f"Subtopic {num} is invalid because it has no value: {subtopic}")
            return False

        if subtopic_name != subtopic_name.lstrip():
            print_error(f"Subtopic {num} is invalid because its name has leading whitespace: {subtopic!r}")
            return False

        if subtopic_name in seen:
            print_error(f"Subtopic {num} is invalid because its name is a duplicate: {subtopic}")
            return False
        seen.add(subtopic_name)

    return True


def list_subtopics(topic: str, max_sections: Optional[int] = None, max_attempts: int = 2) -> list[str]:
    """Return the list of subtopics for the given topic.

    Params:
    * `max_attempts`: If greater than 1, and if the first attempt obtains no subtopics, subsequent attempt(s) will be made. Only the first attempt tries to read from the disk cache.

    `LanguageModelOutputError` is raised if the model output has an error.
    The subclass `LanguageModelOutputRejectionError` is raised if the output is rejected for the given topic.
    The subclass `LanguageModelOutputStructureError` is raised if the output is structurally invalid.
    """

    if max_sections:
        assert NUM_SECTIONS_MIN <= max_sections <= NUM_SECTIONS_MAX, (max_sections, NUM_SECTIONS_MIN, NUM_SECTIONS_MAX)
    restriction = ("\n\n" + PROMPTS["list_subtopics_limit"].format(max_sections=max_sections)) if max_sections else ""

    prompt_name = "list_subtopics"
    prompt = PROMPTS[prompt_name].format(topic=topic, optional_restriction=restriction)
    none_subtopics = ("none", "none.")
    invalid_subtopics = ("", *none_subtopics)
    rejection_error_prefix = "RequestError: "  # Defined in prompt.

    for num_attempt in range(1, max_attempts + 1):
        response = get_cached_content(prompt, read_cache=num_attempt == 1, cache_key_prefix=f"0. {prompt_name}", cache_path=get_topic_work_path(topic))
        assert response, response

        assert response.lower() not in none_subtopics, response
        if response.startswith(rejection_error_prefix):
            rejection_reason = response.removeprefix(rejection_error_prefix).strip()
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputRejectionError(f"Failed to obtain subtopics after {max_attempts} attempts: {rejection_reason}")
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts}: {rejection_reason}")
                continue
        assert not response.lower().startswith(rejection_error_prefix.lower()), response

        subtopics = [s.strip() for s in response.splitlines() if s.strip().lower() not in invalid_subtopics]  # Note: A terminal "None" line has been observed with valid subtopics before it.

        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            subtopics_list_is_valid = is_subtopics_list_valid(subtopics, max_sections)
        if not subtopics_list_is_valid:
            error = error.getvalue().rstrip().removeprefix("Error: ")
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} while listing subtopics: {error}")
                # Note: This condition has been observed with the subtopic list not being numbered correctly.
                continue

        break

    assert subtopics
    return subtopics


def is_subtopic_text_valid(text: str, numbered_name: str) -> bool:
    """Return true if the subtopic text is structurally valid, otherwise false.

    A validation error is printed if the subtopic text is invalid.
    """
    if not text:
        print_error(f"Subtopic {numbered_name!r} is empty.")
        return False

    if text != text.rstrip():
        print_error(f"Subtopic {numbered_name!r} has leading or trailing whitespace.")
        return False

    if text.startswith("\n```"):
        print_error(f"Subtopic {numbered_name!r} may contain a code block.")
        return False

    return True


def get_subtopic(*, topic: str, subtopics: list[str], subtopic: str, strategy: str = "oneshot", max_attempts: int = 3) -> str:
    """Return the full text for a given subtopic within the context of the given topic and list of subtopics."""
    assert subtopic[0].isdigit()  # Is numbered.
    common_kwargs = {"strategy": strategy, "cache_key_prefix": subtopic, "cache_path": get_topic_work_path(topic)}
    subtopics_str = "\n".join(subtopics)

    for num_attempt in range(1, max_attempts + 1):
        match strategy:
            case "oneshot":
                prompt = PROMPTS["generate_subtopic"].format(optional_continuation="", topic=topic, subtopics=subtopics_str, numbered_subtopic=subtopic)
                text = get_cached_content(prompt, read_cache=num_attempt == 1, **common_kwargs)
            case "multishot":  # Observed to never really benefit or produce longer content relative to oneshot.
                prompt = PROMPTS["generate_subtopic"].format(optional_continuation="\n\n" + PROMPTS["continuation_first"], topic=topic, subtopics=subtopics_str, numbered_subtopic=subtopic)
                text = get_cached_content(prompt, read_cache=num_attempt == 1, **common_kwargs, max_completions=5, update_prompt=False)
            case _:
                assert ValueError(f"Invalid strategy: {strategy}")
        text = text.rstrip()

        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            subtopic_text_is_valid = is_subtopic_text_valid(text, numbered_name=subtopic)
        if not subtopic_text_is_valid:
            error = error.getvalue().rstrip().removeprefix("Error: ")
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} while getting subtopic text: {error}")
                continue

        break

    assert text
    return text


def get_subtopics_texts(*, topic: str, subtopics: Optional[list[str]] = None) -> dict[str, str]:
    """Return the ordered full text for all subtopics within the context of the given topic and optional ordered list of subtopics.

    If the list of subtopics is not provided, it is read.
    """
    if not subtopics:
        subtopics = list_subtopics(topic)
    if MAX_CONCURRENT_WORKERS == 1:
        subtopics_texts = {s: get_subtopic(topic=topic, subtopics=subtopics, subtopic=s) for s in subtopics}
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_get_subtopic = lambda subtopic: get_subtopic(topic=topic, subtopics=subtopics, subtopic=subtopic)
            subtopics_texts = {s: text for s, text in zip(subtopics, executor.map(fn_get_subtopic, subtopics))}
    return subtopics_texts


def get_subtopics_speech_texts(*, topic: str, subtopics: Optional[list[str]] = None, markers: Optional[bool] = True) -> dict[str, str]:
    """Return the ordered speech text for all subtopics within the context of the given topic and optional ordered list of subtopics.

    If the list of subtopics is not provided, it is read.

    If markers are enabled, markers are placed at the start of each subtopic section and at the end of the last subtopic section. If markers are disabled, they are not placed, and the disclaimer is moved from the beginning of the first section to the end of the last section.
    """
    if not subtopics:
        subtopics = list_subtopics(topic)
    subtopics_texts = get_subtopics_texts(topic=topic, subtopics=subtopics)

    mark = (lambda marker: marker) if markers else (lambda marker: "")
    demark = (lambda marker: "") if markers else (lambda marker: marker)

    process_subtopic_name = (lambda subtopic_name: subtopic_name.replace(".", ":", 1)) if markers else (lambda subtopic_name: subtopic_name.partition(". ")[2])
    # Note: The section number is removed altogether from the subtopic name if markers are disabled. This is because the number risks not being correctly spoken in an intended foreign language, especially so for non-Latin languages.

    subtopics_speech_texts = {subtopic_name: f'{mark('Section ')}{process_subtopic_name(subtopic_name)}:\n\n{subtopic_text} {{pause}}' for subtopic_name, subtopic_text in subtopics_texts.items()}
    # Note: A pause at the beginning is skipped by the TTS generator, but it is not skipped if at the end, and so it is kept at the end.

    subtopics_speech_texts[subtopics[0]] = f'{topic}:\n\n{{pause}}\n{mark(f'{PROMPTS['tts_disclaimer']} {{pause}}\n\n')}{subtopics_speech_texts[subtopics[0]]}'
    # Note: TTS disclaimer about AI generated audio is required by OpenAI as per https://platform.openai.com/docs/guides/text-to-speech/do-i-own-the-outputted-audio-files
    # Note: It has proven more reliable for the pause to be structured in this way for section 1, rather than be in the leading topic line.
    # Note: If markers are disabled, such as for foreign language use, the disclaimer is skipped from the beginning of the first section (to the end of the last section)
    #       because otherwise the disclaimer can risk conditioning the TTS to speak "1" in English instead of in the foreign language.

    subtopics_speech_texts[subtopics[-1]] = f"{subtopics_speech_texts[subtopics[-1]]}{mark('\n\nThe end.')}{demark(f'\n\n{{pause}}\n{PROMPTS['tts_disclaimer']}')}"
    # Note: "The end." sounds better with the paragraph break before it.
    # Note: Square brackets around "The end." caused the TTS to skip the enclosed text at times.

    return subtopics_speech_texts
