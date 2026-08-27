import concurrent.futures
import contextlib
import io
import json
import re

import podgenai.exceptions
from podgenai.config import MAX_CONCURRENT_WORKERS, MAX_TEXT_LENGTH_IN_FILENAME, NUM_SECTIONS_MAX, NUM_SECTIONS_MIN, PROMPTS
from podgenai.types import SpeechLine, SubtopicDuologue, SubtopicText
from podgenai.util.openai import get_cached_content
from podgenai.util.sys import print_error, print_warning
from podgenai.work import get_topic_work_path

_NUMBERED_SUBTOPIC_PATTERN = re.compile(r"^\d+\. \S.*$")  # Matches a numbered subtopic, e.g. "12. Foo bar".


def is_subtopics_list_valid(subtopics: list[str], max_sections: int | None) -> bool:
    """Return true if the subtopics are structurally valid, otherwise false.

    A validation error is printed if a subtopic is invalid.
    """
    if not subtopics:
        return print_error("No subtopics exist.")

    if (max_sections is not None) and (len(subtopics) > max_sections):
        return print_error(f"Up to {max_sections} subtopics are allowed, but {len(subtopics)} exist.")

    seen = set()
    for num, subtopic in enumerate(subtopics, start=1):
        if subtopic != subtopic.strip():
            return print_error(f"Subtopic {num} is invalid because it has leading or trailing whitespace: {subtopic!r}")

        if not _NUMBERED_SUBTOPIC_PATTERN.match(subtopic):
            return print_error(f"Subtopic {num} is invalid because it is not structured correctly: {subtopic}")

        expected_num_prefix = f"{num}. "
        if not subtopic.startswith(expected_num_prefix):
            return print_error(f"Subtopic {num} is invalid because it is not numbered correctly: {subtopic}")

        subtopic_name = subtopic.removeprefix(expected_num_prefix).strip()
        if not subtopic_name:
            return print_error(f"Subtopic {num} is invalid because it has no value: {subtopic}")

        if subtopic_name != subtopic_name.lstrip():
            return print_error(f"Subtopic {num} is invalid because its name has leading whitespace: {subtopic!r}")

        if subtopic_name in seen:
            return print_error(f"Subtopic {num} is invalid because its name is a duplicate: {subtopic}")
        seen.add(subtopic_name)

    return True


def list_subtopics(topic: str, max_sections: int | None = None, max_attempts: int = 2) -> list[str]:
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
        response = get_cached_content(prompt, read_cache=num_attempt == 1, cache_key_prefix=f"0. {prompt_name}", cache_path=get_topic_work_path(topic), temperature=0.5, verbosity="low")
        # Note: temperature=0.5 is specified in an attempt to increase the objectivity of the list of subtopics.
        # Note: verbosity=low is specified in an attempt to reduce an excessive number of subtopics.
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


def is_subtopic_monologue_valid(monologue: str, numbered_name: str) -> bool:
    """Return true if the subtopic monologue is structurally valid, otherwise false.

    A validation error is printed if the subtopic monologue is invalid.
    """
    assert _NUMBERED_SUBTOPIC_PATTERN.match(numbered_name), numbered_name
    if not monologue:
        return print_error(f"Subtopic monologue {numbered_name!r} is empty.")

    if monologue != monologue.rstrip():
        return print_error(f"Subtopic monologue {numbered_name!r} has leading or trailing whitespace.")

    checked_monologue = "\n" + monologue
    if "\n```" in checked_monologue:
        return print_error(f"Subtopic monologue {numbered_name!r} may contain a code block.")
    if ("\n## " in checked_monologue) or ("\n### " in checked_monologue):
        return print_error(f"Subtopic monologue {numbered_name!r} may contain a markdown section header.")
    if ("\n* " in checked_monologue) or ("\n- " in checked_monologue) or ("\n• " in checked_monologue):
        return print_error(f"Subtopic monologue {numbered_name!r} may contain a markdown list item.")

    return True


def is_unmarked_subtopic_duologue_valid(duologue: str, numbered_name: str, boundary_voice_sex: str, non_boundary_voice_sex: str) -> bool:
    """Return true if the unmarked subtopic duologue is structurally valid, otherwise false.

    A validation error is printed if the subtopic duologue is invalid.
    """
    assert _NUMBERED_SUBTOPIC_PATTERN.match(numbered_name), numbered_name

    if not duologue:
        return print_error(f"Subtopic duologue {numbered_name!r} is empty.")

    if duologue != duologue.rstrip():
        return print_error(f"Subtopic duologue {numbered_name!r} has leading or trailing whitespace.")

    lines = [line for line in io.StringIO(duologue) if line.strip()]
    num_lines = len(lines)
    if not num_lines:
        return print_error(f"Subtopic duologue {numbered_name!r} is invalid because it has no lines.")

    expected_keys = ("speaker", "speech", "tone")
    expected_speakers = (boundary_voice_sex, non_boundary_voice_sex)
    prev_speaker = None
    for line_number, line in enumerate(lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            return print_error(f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} is not valid JSON: {exc.msg} at column {exc.colno}.")

        if not isinstance(obj, dict):
            return print_error(f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} is not a JSON dictionary.")
        for key in expected_keys:
            if key not in obj:
                return print_error(f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} is missing the required property {key!r}.")
        for key in obj:
            if key not in expected_keys:
                print_warning(f"Subtopic duologue {numbered_name!r} has line {line_number} with an unexpected property {key!r} having value: {obj[key]!r}")

        speaker = obj["speaker"]
        if speaker not in expected_speakers:
            return print_error(f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} has an invalid speaker: {speaker!r}.")
        if (line_number == 1) and (speaker != boundary_voice_sex):
            return print_error(f"Subtopic duologue {numbered_name!r} is invalid because the first speaker must be {boundary_voice_sex!r}, but was {speaker!r}.")
        if (line_number == num_lines) and (speaker != boundary_voice_sex):
            return print_error(f"Subtopic duologue {numbered_name!r} is invalid because the last speaker must be {boundary_voice_sex!r}, but was {speaker!r}.")
        if speaker == prev_speaker:
            print_warning(f"Subtopic duologue {numbered_name!r} has line {line_number} with the same speaker as the previous line: {speaker!r}.")
        prev_speaker = speaker

        speech = obj["speech"]
        if not isinstance(speech, str) or not speech.strip():
            return print_error(f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} has invalid speech: {speech!r}.")

        tone = obj["tone"]
        if not isinstance(tone, str) or not tone.strip():
            return print_error(f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} has invalid tone instructions: {tone!r}.")

    return True


def get_subtopic_monologue(*, topic: str, subtopics: list[str], subtopic: str, max_attempts: int = 3) -> str:
    """Return the monologue for a given subtopic within the context of the given topic and list of subtopics."""
    assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic), subtopic
    common_kwargs = {"cache_key_prefix": f"{subtopic[:MAX_TEXT_LENGTH_IN_FILENAME].rstrip()} (monologue)", "cache_path": get_topic_work_path(topic), "temperature": 0.5, "verbosity": "low"}
    # Note: temperature=0.5 is specified in an attempt to increase the objectivity of the monologue.
    # Note: verbosity=low is specified in an attempt to reduce an excessively long monologue.
    subtopics_str = "\n".join(subtopics)

    for num_attempt in range(1, max_attempts + 1):
        prompt = PROMPTS["generate_subtopic_monologue"].format(topic=topic, subtopics=subtopics_str, numbered_subtopic=subtopic)
        monologue = get_cached_content(prompt, read_cache=num_attempt == 1, **common_kwargs)
        monologue = monologue.rstrip()

        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            subtopic_monologue_is_valid = is_subtopic_monologue_valid(monologue, numbered_name=subtopic)
        if not subtopic_monologue_is_valid:
            error = error.getvalue().rstrip().removeprefix("Error: ")
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} while getting subtopic monologue: {error}")
                continue

        break

    assert monologue
    return monologue


def get_subtopic_duologue(*, topic: str, subtopics: list[str], subtopic: str, subtopic_monologue: str, boundary_voice_sex: str, non_boundary_voice_sex: str, max_attempts: int = 3) -> list[SpeechLine]:
    """Return the duologue for a given subtopic within the context of the given topic and list of subtopics."""
    assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic), subtopic
    common_kwargs = {"cache_key_prefix": f"{subtopic[:MAX_TEXT_LENGTH_IN_FILENAME].rstrip()} (duologue)", "cache_path": get_topic_work_path(topic)}
    subtopics_str = "\n".join(subtopics)

    for num_attempt in range(1, max_attempts + 1):
        prompt = PROMPTS["generate_subtopic_duologue"].format(topic=topic, subtopics=subtopics_str, numbered_subtopic=subtopic, subtopic_monologue=subtopic_monologue, boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)
        duologue = get_cached_content(prompt, read_cache=num_attempt == 1, **common_kwargs)  # Default temperature and verbosity are used for duologue, considering it is derived from the monologue.
        duologue = duologue.rstrip()

        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            subtopic_duologue_is_valid = is_unmarked_subtopic_duologue_valid(duologue, numbered_name=subtopic, boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)
        if not subtopic_duologue_is_valid:
            error = error.getvalue().rstrip().removeprefix("Error: ")
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} while getting subtopic duologue: {error}")
                continue

        break

    assert duologue
    duologue_lines: list[SpeechLine] = [json.loads(line) for line in io.StringIO(duologue) if line.strip()]
    assert duologue_lines
    return duologue_lines


def get_subtopics_duologues(*, topic: str, subtopics_monologues: list[SubtopicText], boundary_voice_sex: str, non_boundary_voice_sex: str) -> list[SubtopicDuologue]:
    """Return the ordered subtopic duologue for each subtopic within the context of the given topic, ordered list of subtopics, and subtopic monologue."""
    assert subtopics_monologues
    if MAX_CONCURRENT_WORKERS == 1:
        subtopic_duologues = [
            SubtopicDuologue(subtopic=s["name"], duologue=get_subtopic_duologue(topic=topic, subtopics=[s["name"] for s in subtopics_monologues], subtopic=s["name"], subtopic_monologue=s["text"], boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)) for s in subtopics_monologues
        ]
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_get_subtopic_duologue = lambda s: get_subtopic_duologue(topic=topic, subtopics=[s["name"] for s in subtopics_monologues], subtopic=s["name"], subtopic_monologue=s["text"], boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)
            subtopic_duologues = [SubtopicDuologue(subtopic=s["name"], duologue=duologue) for s, duologue in zip(subtopics_monologues, executor.map(fn_get_subtopic_duologue, subtopics_monologues))]
    return subtopic_duologues


def get_subtopics_monologues(*, topic: str, subtopics: list[str]) -> list[SubtopicText]:
    """Return the ordered subtopic monologue for each subtopic within the context of the given topic and ordered list of subtopics."""
    assert subtopics
    if MAX_CONCURRENT_WORKERS == 1:
        subtopic_monologues = [SubtopicText(name=s, text=get_subtopic_monologue(topic=topic, subtopics=subtopics, subtopic=s)) for s in subtopics]
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_get_subtopic_monologue = lambda subtopic: get_subtopic_monologue(topic=topic, subtopics=subtopics, subtopic=subtopic)
            subtopic_monologues = [SubtopicText(name=s, text=monologue) for s, monologue in zip(subtopics, executor.map(fn_get_subtopic_monologue, subtopics))]
    return subtopic_monologues


def mark_subtopics_duologues(*, topic: str, subtopics_duologues: list[SubtopicDuologue], markers: bool | None = True, marker_voice_sex: str) -> None:
    """Mark the subtopic duologue for each subtopic within the context of the given topic and ordered list of subtopics.

    If markers are enabled, markers are placed at the start of each subtopic section. The disclaimer is placed at the beginning of the first section.
    If markers are disabled, they are not placed. The disclaimer is placed at the end of the last section.
    """
    assert subtopics_duologues
    assert marker_voice_sex in ("male", "female")

    mark = (lambda marker: marker) if markers else (lambda marker: "")
    demark = (lambda marker: "") if markers else (lambda marker: marker)

    process_subtopic_name = (lambda subtopic_name: subtopic_name.replace(".", ":", 1)) if markers else (lambda subtopic_name: subtopic_name.partition(". ")[2])
    # Note: The section number is removed altogether from the subtopic name if markers are disabled. This is because the number risks not being correctly spoken in an intended foreign language, especially so for non-Latin languages.

    for subtopic_duologue in subtopics_duologues:
        assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic_duologue["subtopic"]), subtopic_duologue["subtopic"]
        subtopic_duologue["duologue"].insert(0, SpeechLine(speaker=marker_voice_sex, speech=f"{mark('Section ')}{process_subtopic_name(subtopic_duologue['subtopic'])}", tone=None))

    subtopics_duologues[0]["duologue"][0]["speech"] = f"{topic}:\n\n{mark(f'{PROMPTS["tts_disclaimer"]}\n\n')}{subtopics_duologues[0]['duologue'][0]['speech']}"
    if not markers:  # This condition check exists to avoid adding an empty SpeechLine if markers are enabled.
        subtopics_duologues[-1]["duologue"].append(SpeechLine(speaker=marker_voice_sex, speech=demark(PROMPTS["tts_disclaimer"]), tone=None))


def get_subtopics_duologues_transcripts(*, subtopics_duologues: list[SubtopicDuologue]) -> list[SubtopicText]:
    """Return the ordered subtopic duologue transcript for each subtopic within the context of the given topic and ordered list of subtopics."""
    assert subtopics_duologues
    return [
        SubtopicText(name=subtopic_duologue["subtopic"], text="\n".join(f"#S{subtopic_num}L{line_num}: [{line['speaker']}] {line['speech']} (tone: {line.get('tone')})" for line_num, line in enumerate(subtopic_duologue["duologue"], start=0))) for subtopic_num, subtopic_duologue in enumerate(subtopics_duologues, start=1)
    ]


def get_subtopics_monologue_transcripts(*, topic: str, subtopic_monologues: list[SubtopicText], markers: bool | None = True) -> list[SubtopicText]:
    """Return the ordered monologue transcript for all subtopics within the context of the given topic and ordered list of subtopics.

    If markers are enabled, markers are placed at the start of each subtopic section. The disclaimer is placed at the beginning of the first section.
    If markers are disabled, they are not placed. The disclaimer is placed at the end of the last section.
    """
    assert subtopic_monologues

    mark = (lambda marker: marker) if markers else (lambda marker: "")
    demark = (lambda marker: "") if markers else (lambda marker: marker)

    process_subtopic_name = (lambda subtopic_name: subtopic_name.replace(".", ":", 1)) if markers else (lambda subtopic_name: subtopic_name.partition(". ")[2])
    # Note: The section number is removed altogether from the subtopic name if markers are disabled. This is because the number risks not being correctly spoken in an intended foreign language, especially so for non-Latin languages.

    for subtopic_monologue in subtopic_monologues:
        assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic_monologue["name"]), subtopic_monologue["name"]
    subtopics_monologue_transcripts = [SubtopicText(name=s["name"], text=f"{mark('Section ')}{process_subtopic_name(s['name'])}:\n\n{s['text']}") for s in subtopic_monologues]

    subtopics_monologue_transcripts[0]["text"] = f"{topic}:\n\n{mark(f'{PROMPTS["tts_disclaimer"]}\n\n')}{subtopics_monologue_transcripts[0]['text']}"
    subtopics_monologue_transcripts[-1]["text"] = f"{subtopics_monologue_transcripts[-1]['text']}{demark(f'\n\n{PROMPTS["tts_disclaimer"]}')}"

    return subtopics_monologue_transcripts
