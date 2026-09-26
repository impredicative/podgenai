import io
import json
import math
import re
from collections.abc import Callable
from pathlib import Path
from typing import NotRequired, TypedDict, cast
from xml.sax.saxutils import quoteattr

import podgenai.exceptions
from podgenai.config import MAX_CONCURRENT_WORKERS, MAX_TEXT_LENGTH_IN_FILENAME, NUM_SECTIONS_MAX, NUM_SECTIONS_MIN, PROMPTS, TTS_DISCLAIMER_W_DOC, TTS_DISCLAIMER_WO_DOC
from podgenai.content.document import get_document_tag
from podgenai.types import DeduplicatedSubtopicText, JSONValue, SpeechLine, SubtopicDuologue, SubtopicMonologueTriple, SubtopicText, VoiceSex
from podgenai.util.contextvars import ContextThreadPoolExecutor

# from podgenai.util.difflib import diff_texts_inline
from podgenai.util.openai import MODELS, get_cached_content
from podgenai.util.sys import print_warning
from podgenai.work import get_topic_work_path

_NUMBERED_SUBTOPIC_PATTERN = re.compile(r"^\d+\. \S.*$")  # Matches a numbered subtopic, e.g. "12. Foo bar".


class _CachedContentKwargs(TypedDict):
    local_cache_key_prefix: str
    cache_path: Path
    remote_cache_key: str
    temperature: float
    verbosity: NotRequired[str]


def is_subtopics_list_valid(subtopics: list[str], max_sections: int | None) -> str | None:
    """Return an error message if the subtopics are structurally invalid, otherwise None."""
    if not subtopics:
        return "No subtopics exist."

    if (max_sections is not None) and (len(subtopics) > max_sections):
        return f"Up to {max_sections} subtopics are allowed, but {len(subtopics)} exist."

    seen: set[str] = set()
    for num, subtopic in enumerate(subtopics, start=1):
        if subtopic != subtopic.strip():
            return f"Subtopic {num} is invalid because it has leading or trailing whitespace: {subtopic!r}"

        if not _NUMBERED_SUBTOPIC_PATTERN.match(subtopic):
            return f"Subtopic {num} is invalid because it is not structured correctly: {subtopic}"

        expected_num_prefix = f"{num}. "
        if not subtopic.startswith(expected_num_prefix):
            return f"Subtopic {num} is invalid because it is not numbered correctly: {subtopic}"

        subtopic_name = subtopic.removeprefix(expected_num_prefix).strip()
        if not subtopic_name:
            return f"Subtopic {num} is invalid because it has no value: {subtopic}"

        if subtopic_name != subtopic_name.lstrip():
            return f"Subtopic {num} is invalid because its name has leading whitespace: {subtopic!r}"

        if subtopic_name in seen:
            return f"Subtopic {num} is invalid because its name is a duplicate: {subtopic}"
        seen.add(subtopic_name)

    return None


def list_subtopics(topic: str, document: str | None = None, max_sections: int | None = None, max_attempts: int = 2) -> list[str]:
    """Return the list of subtopics for the given topic.

    Params:
    * `document`: Contents of a single text or markdown document to use as the exclusive source for the subtopics.  If not given, the subtopics are generated from the model's internal knowledge.
    * `max_sections`: Maximum number of sections to generate.
    * `max_attempts`: If greater than 1, and if the first attempt obtains no subtopics, subsequent attempt(s) will be made. Only the first attempt tries to read from the disk cache.

    `LanguageModelOutputError` is raised if the model output has an error.
    The subclass `LanguageModelOutputRejectionError` is raised if the output is rejected for the given topic.
    The subclass `LanguageModelOutputStructureError` is raised if the output is structurally invalid.
    """

    if max_sections is not None:
        assert NUM_SECTIONS_MIN <= max_sections <= NUM_SECTIONS_MAX, (max_sections, NUM_SECTIONS_MIN, NUM_SECTIONS_MAX)

    prompt_name = "list_subtopics"
    document_tag = get_document_tag(document) if document is not None else None
    prompt = PROMPTS[prompt_name].render(topic=topic, max_sections=max_sections, source=document, source_tag=document_tag)
    none_subtopics = ("none", "none.")
    invalid_subtopics = ("", *none_subtopics)
    rejection_error_prefix = "RequestError: "  # Defined in prompt.
    reasoning_effort = ["none", "low"][0]  # Note: reasoning_effort=none is demonstrably sufficient at least when not having a document.
    local_cache_key_prefix = f"0. {prompt_name}"
    remote_cache_key = prompt_name if document is None else f"{prompt_name}:from_document"

    temperature = 0.5 if (reasoning_effort == "none") else 1
    # Note: temperature=0.5 is specified in an attempt to increase the objectivity of the list of subtopics.
    # temperature=0.5 is not supported with reasoning_effort!=none.

    for num_attempt in range(1, max_attempts + 1):
        response = get_cached_content(prompt, read_cache=num_attempt == 1, local_cache_key_prefix=local_cache_key_prefix, cache_path=get_topic_work_path(topic), temperature=temperature, reasoning_effort=reasoning_effort, verbosity="low", remote_cache_key=remote_cache_key)
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

        validation_error = is_subtopics_list_valid(subtopics, max_sections)
        if validation_error is not None:
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(validation_error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} while listing subtopics: {validation_error}")
                # Note: This condition has been observed with the subtopic list not being numbered correctly.
                continue

        break

    assert subtopics
    return subtopics


def is_subtopic_monologue_valid(monologue: str, numbered_name: str) -> str | None:
    """Return an error message if the subtopic monologue is structurally invalid, otherwise None."""
    assert _NUMBERED_SUBTOPIC_PATTERN.match(numbered_name), numbered_name
    if not monologue:
        return f"Subtopic monologue {numbered_name!r} is empty."

    if monologue != monologue.rstrip():
        return f"Subtopic monologue {numbered_name!r} has leading or trailing whitespace."

    checked_monologue = "\n" + monologue
    if "\n```" in checked_monologue:
        return f"Subtopic monologue {numbered_name!r} may contain a code block."
    if ("\n## " in checked_monologue) or ("\n### " in checked_monologue):
        return f"Subtopic monologue {numbered_name!r} may contain a markdown section header."
    if ("\n* " in checked_monologue) or ("\n- " in checked_monologue) or ("\n• " in checked_monologue):
        return f"Subtopic monologue {numbered_name!r} may contain a markdown list item."

    if monologue.startswith("<segment_monologue") or monologue.endswith("</segment_monologue>"):
        return f"Subtopic monologue {numbered_name!r} contains a segment monologue tag."

    return None


def is_unmarked_subtopic_duologue_valid(duologue: str, numbered_name: str, boundary_voice_sex: VoiceSex, non_boundary_voice_sex: VoiceSex) -> str | None:
    """Return an error message if the unmarked subtopic duologue is structurally invalid, otherwise None."""
    assert _NUMBERED_SUBTOPIC_PATTERN.match(numbered_name), numbered_name

    if not duologue:
        return f"Subtopic duologue {numbered_name!r} is empty."

    if duologue != duologue.rstrip():
        return f"Subtopic duologue {numbered_name!r} has leading or trailing whitespace."

    lines = [line for line in io.StringIO(duologue) if line.strip()]
    num_lines = len(lines)
    if not num_lines:
        return f"Subtopic duologue {numbered_name!r} is invalid because it has no lines."

    expected_keys = ("speaker", "speech", "tone")
    expected_speakers = (boundary_voice_sex, non_boundary_voice_sex)
    prev_speaker: VoiceSex | None = None
    for line_number, line in enumerate(lines, start=1):
        try:
            obj: JSONValue = json.loads(line)
        except json.JSONDecodeError as exc:
            return f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} is not valid JSON: {exc.msg} at column {exc.colno}."

        if not isinstance(obj, dict):
            return f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} is not a JSON dictionary."
        for key in expected_keys:
            if key not in obj:
                return f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} is missing the required property {key!r}."
        for key in obj:
            if key not in expected_keys:
                print_warning(f"Subtopic duologue {numbered_name!r} has line {line_number} with an unexpected property {key!r} having value: {obj[key]!r}")

        speaker = obj["speaker"]
        if speaker not in expected_speakers:
            return f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} has an invalid speaker: {speaker!r}."
        if (line_number == 1) and (speaker != boundary_voice_sex):
            return f"Subtopic duologue {numbered_name!r} is invalid because the first speaker must be {boundary_voice_sex!r}, but was {speaker!r}."
        if (line_number == num_lines) and (speaker != boundary_voice_sex):
            return f"Subtopic duologue {numbered_name!r} is invalid because the last speaker must be {boundary_voice_sex!r}, but was {speaker!r}."
        if speaker == prev_speaker:
            print_warning(f"Subtopic duologue {numbered_name!r} has line {line_number} with the same speaker as the previous line: {speaker!r}.")
        prev_speaker = cast(VoiceSex, speaker)

        speech = obj["speech"]
        if not isinstance(speech, str) or not speech.strip():
            return f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} has invalid speech: {speech!r}."

        tone = obj["tone"]
        if not isinstance(tone, str) or not tone.strip():
            return f"Subtopic duologue {numbered_name!r} is invalid because line {line_number} has invalid tone instructions: {tone!r}."

    return None


def get_subtopic_monologue(*, topic: str, document: str | None = None, subtopics: list[str], subtopic: str, max_attempts: int = 3) -> str:
    """Return the monologue for a given subtopic within the context of the given topic and list of subtopics."""
    assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic), subtopic
    # Note: temperature=0.5 is specified in an attempt to increase the objectivity of the monologue.
    # Note: verbosity=low is specified in an attempt to reduce an excessively long monologue.
    subtopics_str = "\n".join(subtopics)
    model = MODELS["text"] if document else MODELS["knowledge"]
    document_tag = get_document_tag(document) if document is not None else None
    # Note: The knowledge model is used for subtopic monologue generation only when the document is not present. This is due to a prohibitive cost of using the knowledge model for each subtopic when the document is present.
    prompt_name = "generate_subtopic_monologue"
    prompt = PROMPTS[prompt_name].render(topic=topic, subtopics=subtopics_str, numbered_subtopic=subtopic, source=document, source_tag=document_tag)
    remote_cache_key = prompt_name if document is None else f"{prompt_name}:from_document"
    common_kwargs: _CachedContentKwargs = {"local_cache_key_prefix": f"{subtopic[:MAX_TEXT_LENGTH_IN_FILENAME].rstrip()} (monologue)", "cache_path": get_topic_work_path(topic), "temperature": 0.5, "verbosity": "low", "remote_cache_key": remote_cache_key}

    for num_attempt in range(1, max_attempts + 1):
        monologue = get_cached_content(prompt, read_cache=num_attempt == 1, model=model, **common_kwargs)
        monologue = monologue.rstrip()

        validation_error = is_subtopic_monologue_valid(monologue, numbered_name=subtopic)
        if validation_error is not None:
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(validation_error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} while getting subtopic monologue: {validation_error}")
                continue

        break

    assert monologue
    return monologue


def deduplicate_subtopic_monologue(*, topic: str, subtopics: list[str], subtopic_monologue_triple: SubtopicMonologueTriple, iteration: int, max_attempts: int = 3) -> DeduplicatedSubtopicText:
    """Return the deduplication result for the current monologue in one triple.

    The previous and next monologues are read-only context. The returned value
    contains either a revised current monologue that still requires another
    iteration, or the unchanged current monologue marked as deduplicated.

    A segment is permanently retired only after the model returns OK
    or returns text identical to that segment's current text.
    """
    assert iteration >= 1, iteration
    assert max_attempts >= 1, max_attempts

    positions = ("previous", "current", "next")
    cache_path = get_topic_work_path(topic)
    subtopics_str = "\n".join(subtopics)
    _, subtopic_monologue_curr, _ = subtopic_monologue_triple
    subtopic = subtopic_monologue_curr["name"]
    assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic), subtopic

    segments_xml = ["<segment_monologues>"]
    for idx, subtopic_monologue in enumerate(subtopic_monologue_triple):
        if subtopic_monologue is None:
            continue
        position = positions[idx]
        title = quoteattr(subtopic_monologue["name"])
        assert title == title.strip()
        segments_xml.append(f'\n<segment_monologue position="{position}" title={title}>')
        monologue = subtopic_monologue["text"]
        assert monologue == monologue.strip()
        segments_xml.append(monologue)  # Intentionally not escaped using xml.sax.saxutils.escape.
        segments_xml.append("</segment_monologue>")
    segments_xml.append("\n</segment_monologues>")
    segments_xml_str = "\n".join(segments_xml)

    prompt_name = "dedup_subtopic_monologue"
    common_kwargs: _CachedContentKwargs = {"local_cache_key_prefix": f"{subtopic[:MAX_TEXT_LENGTH_IN_FILENAME].rstrip()} (monologue) (dedup {iteration})", "cache_path": cache_path, "remote_cache_key": prompt_name, "temperature": 0.0}
    # Note: temperature=0.0 is specified in an attempt to minimize the iterations required for deduplication.
    prompt = PROMPTS[prompt_name].render(topic=topic, subtopics=subtopics_str, numbered_subtopic=subtopic, segments_xml=segments_xml_str)

    for num_attempt in range(1, max_attempts + 1):
        monologue = get_cached_content(prompt, read_cache=num_attempt == 1, model=MODELS["text"], **common_kwargs)
        monologue = monologue.rstrip()
        if (monologue.strip('"') in ("OK", "OK.", "O.K.")) or (monologue == subtopic_monologue_curr["text"]):
            return DeduplicatedSubtopicText(name=subtopic, text=subtopic_monologue_curr["text"], is_deduplicated=True)

        validation_error = is_subtopic_monologue_valid(monologue, numbered_name=subtopic)
        if validation_error is not None:
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(validation_error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} in iteration {iteration} while getting deduplicated subtopic monologue: {validation_error}")
                continue

        # Note: Sometimes the monologue increases slightly in length, and this is okay because it adds useful context.
        return DeduplicatedSubtopicText(name=subtopic, text=monologue, is_deduplicated=False)

    raise AssertionError("Deduplication attempts unexpectedly exhausted.")


def deduplicate_subtopics_monologues(*, topic: str, subtopics_monologues: list[SubtopicText], max_attempts: int = 3) -> list[SubtopicText]:  # pyright: ignore[reportRedeclaration]
    """Return the deduplicated subtopic monologue texts.

    Each iteration has these phases:
    * Process odd-numbered (red) current segments concurrently, then commit all red results.
    * Process even-numbered (black) current segments concurrently, then commit all black results.
    Every call in a phase reads the same immutable snapshot.

    The maximum allowable number of iterations is set to the number of subtopics.
    """
    assert MAX_CONCURRENT_WORKERS >= 1, MAX_CONCURRENT_WORKERS
    num_subtopics = len(subtopics_monologues)
    subtopics = [subtopic_monologue["name"] for subtopic_monologue in subtopics_monologues]
    max_iterations: int | None = [math.ceil(2 * math.log2(num_subtopics)), math.ceil(2 * math.sqrt(num_subtopics)), None][0]  # Empirically satisfactory safeguard. log2 is more conservative than sqrt. Set to None to disable.

    subtopics_monologues: list[DeduplicatedSubtopicText] = [DeduplicatedSubtopicText(**s, is_deduplicated=False) for s in subtopics_monologues]

    iteration = 0
    original_subtopics_monologues_size = sum(len(subtopic["text"]) for subtopic in subtopics_monologues)
    print(f"At iteration {iteration}, subtopic monologues have a combined size of {original_subtopics_monologues_size:,} characters.")
    while True:
        iteration += 1
        if max_iterations is not None:
            assert max_iterations >= 0
            if iteration > max_iterations:
                print_warning(f"Exhausted a max of {max_iterations} iterations while deduplicating subtopic monologues.")
                break
            # if iteration > 1:
            #     get_confirmation(f"iteration {iteration}")
        for phase_start_index in (0, 1):  # Odd (red) segment numbers first, then even (black) segment numbers.
            current_indices = [idx for idx in range(phase_start_index, num_subtopics, 2) if not subtopics_monologues[idx]["is_deduplicated"]]
            if not current_indices:
                continue

            # No object in this snapshot is mutated. All results are collected before any are committed, which forms the phase barrier.
            phase_snapshot = [SubtopicText(name=s["name"], text=s["text"]) for s in subtopics_monologues]
            subtopic_monologue_triples: list[SubtopicMonologueTriple] = [
                (
                    phase_snapshot[idx - 1] if (idx > 0) else None,
                    phase_snapshot[idx],
                    phase_snapshot[idx + 1] if (idx + 1) < num_subtopics else None,
                )
                for idx in current_indices
            ]
            fn_deduplicate_subtopic_monologue: Callable[[SubtopicMonologueTriple], DeduplicatedSubtopicText] = lambda triple, iteration=iteration: deduplicate_subtopic_monologue(
                topic=topic,
                subtopics=subtopics,
                subtopic_monologue_triple=triple,
                iteration=iteration,
                max_attempts=max_attempts,
            )

            if MAX_CONCURRENT_WORKERS == 1:
                phase_results = [fn_deduplicate_subtopic_monologue(triple) for triple in subtopic_monologue_triples]
            else:
                with ContextThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
                    phase_results = list(executor.map(fn_deduplicate_subtopic_monologue, subtopic_monologue_triples))

            assert len(current_indices) == len(phase_results)
            for current_index, phase_result in zip(current_indices, phase_results):
                # diff = diff_texts_inline(subtopics_monologues[current_index]["text"], phase_result["text"])
                # print(f"Diff between previous monologue ({len(subtopics_monologues[current_index]['text']):,} chars) and current monologue ({len(phase_result['text']):,} chars) as of iteration {iteration} for subtopic: {phase_result['name']}:\n>>>DIFF BEGIN\n{diff}\n<<<DIFF END")
                # get_confirmation("monologue text deduplication")

                assert phase_result["name"] == subtopics_monologues[current_index]["name"]
                subtopics_monologues[current_index] = phase_result

        subtopics_monologues_size = sum(len(subtopic["text"]) for subtopic in subtopics_monologues)
        subtopics_monologues_size_ratio = subtopics_monologues_size / original_subtopics_monologues_size
        if all(subtopic_monologue["is_deduplicated"] for subtopic_monologue in subtopics_monologues):
            print(f"All {num_subtopics} subtopic monologues are deduplicated after iteration {iteration}/{max_iterations}, cumulatively having {subtopics_monologues_size_ratio:.2%} of the original length.")
            break
        else:
            num_deduplicated = sum(subtopic_monologue["is_deduplicated"] for subtopic_monologue in subtopics_monologues)
            print(f"After iteration {iteration}/{max_iterations}, only {num_deduplicated}/{num_subtopics} subtopic monologues are deduplicated, cumulatively having {subtopics_monologues_size_ratio:.2%} of the original length.")

    subtopic_monologues: list[SubtopicText] = [SubtopicText(name=subtopic_monologue["name"], text=subtopic_monologue["text"]) for subtopic_monologue in subtopics_monologues]
    return subtopic_monologues


def get_subtopic_duologue(*, topic: str, subtopics: list[str], subtopic: str, subtopic_monologue: str, boundary_voice_sex: VoiceSex, non_boundary_voice_sex: VoiceSex, max_attempts: int = 3) -> list[SpeechLine]:
    """Return the duologue for a given subtopic within the context of the given topic and list of subtopics."""
    assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic), subtopic
    local_cache_key_prefix = f"{subtopic[:MAX_TEXT_LENGTH_IN_FILENAME].rstrip()} (duologue)"
    cache_path = get_topic_work_path(topic)
    subtopics_str = "\n".join(subtopics)
    prompt_name = "generate_subtopic_duologue"
    prompt = PROMPTS[prompt_name].render(topic=topic, subtopics=subtopics_str, numbered_subtopic=subtopic, subtopic_monologue=subtopic_monologue, boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)

    for num_attempt in range(1, max_attempts + 1):
        duologue = get_cached_content(prompt, read_cache=num_attempt == 1, local_cache_key_prefix=local_cache_key_prefix, cache_path=cache_path, remote_cache_key=prompt_name)  # Default temperature and verbosity are used for duologue, considering it is derived from the monologue.
        duologue = duologue.rstrip()

        validation_error = is_unmarked_subtopic_duologue_valid(duologue, numbered_name=subtopic, boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)
        if validation_error is not None:
            if num_attempt == max_attempts:
                raise podgenai.exceptions.LanguageModelOutputStructureError(validation_error)
            else:
                print_warning(f"Fault in attempt {num_attempt} of {max_attempts} while getting subtopic duologue: {validation_error}")
                continue

        break

    assert duologue
    duologue_lines: list[SpeechLine] = [json.loads(line) for line in io.StringIO(duologue) if line.strip()]
    assert duologue_lines
    return duologue_lines


def get_subtopics_duologues(*, topic: str, subtopics_monologues: list[SubtopicText], boundary_voice_sex: VoiceSex, non_boundary_voice_sex: VoiceSex) -> list[SubtopicDuologue]:
    """Return the ordered subtopic duologue for each subtopic within the context of the given topic, ordered list of subtopics, and subtopic monologue."""
    assert subtopics_monologues
    if MAX_CONCURRENT_WORKERS == 1:
        subtopic_duologues = [
            SubtopicDuologue(subtopic=s["name"], duologue=get_subtopic_duologue(topic=topic, subtopics=[s["name"] for s in subtopics_monologues], subtopic=s["name"], subtopic_monologue=s["text"], boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)) for s in subtopics_monologues
        ]
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with ContextThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_get_subtopic_duologue: Callable[[SubtopicText], list[SpeechLine]] = lambda s: get_subtopic_duologue(topic=topic, subtopics=[s["name"] for s in subtopics_monologues], subtopic=s["name"], subtopic_monologue=s["text"], boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)
            subtopic_duologues = [SubtopicDuologue(subtopic=s["name"], duologue=duologue) for s, duologue in zip(subtopics_monologues, executor.map(fn_get_subtopic_duologue, subtopics_monologues))]
    return subtopic_duologues


def get_subtopics_monologues(*, topic: str, document: str | None = None, subtopics: list[str]) -> list[SubtopicText]:
    """Return the ordered subtopic monologue for each subtopic within the context of the given topic and ordered list of subtopics."""
    assert subtopics
    if MAX_CONCURRENT_WORKERS == 1:
        subtopic_monologues = [SubtopicText(name=s, text=get_subtopic_monologue(topic=topic, document=document, subtopics=subtopics, subtopic=s)) for s in subtopics]
    else:
        assert MAX_CONCURRENT_WORKERS > 1
        with ContextThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as executor:
            fn_get_subtopic_monologue: Callable[[str], str] = lambda subtopic: get_subtopic_monologue(topic=topic, document=document, subtopics=subtopics, subtopic=subtopic)
            subtopic_monologues = [SubtopicText(name=s, text=monologue) for s, monologue in zip(subtopics, executor.map(fn_get_subtopic_monologue, subtopics))]
    return subtopic_monologues


def mark_subtopics_duologues(*, topic: str, is_from_document: bool, subtopics_duologues: list[SubtopicDuologue], markers: bool = True, marker_voice_sex: VoiceSex) -> None:
    """Mark the subtopic duologue for each subtopic within the context of the given topic and ordered list of subtopics.

    If markers are enabled, markers are placed at the start of each subtopic section. The disclaimer is placed at the beginning of the first section.
    If markers are disabled, they are not placed. The disclaimer is placed at the end of the last section.
    """
    assert subtopics_duologues
    assert marker_voice_sex in ("male", "female")

    mark: Callable[[str], str] = (lambda marker: marker) if markers else (lambda marker: "")
    demark: Callable[[str], str] = (lambda marker: "") if markers else (lambda marker: marker)

    process_subtopic_name: Callable[[str], str] = (lambda subtopic_name: subtopic_name.replace(".", ":", 1)) if markers else (lambda subtopic_name: subtopic_name.partition(". ")[2])
    # Note: The section number is removed altogether from the subtopic name if markers are disabled. This is because the number risks not being correctly spoken in an intended foreign language, especially so for non-Latin languages.

    for subtopic_duologue in subtopics_duologues:
        assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic_duologue["subtopic"]), subtopic_duologue["subtopic"]
        subtopic_duologue["duologue"].insert(0, SpeechLine(speaker=marker_voice_sex, speech=f"{mark('Section ')}{process_subtopic_name(subtopic_duologue['subtopic'])}", tone=None))

    tts_disclaimer = TTS_DISCLAIMER_W_DOC if is_from_document else TTS_DISCLAIMER_WO_DOC
    subtopics_duologues[0]["duologue"][0]["speech"] = f"{topic}:\n\n{mark(f'{tts_disclaimer}\n\n')}{subtopics_duologues[0]['duologue'][0]['speech']}"
    if not markers:  # This condition check exists to avoid adding an empty SpeechLine if markers are enabled.
        subtopics_duologues[-1]["duologue"].append(SpeechLine(speaker=marker_voice_sex, speech=demark(tts_disclaimer), tone=None))


def get_subtopics_duologues_transcripts(*, subtopics_duologues: list[SubtopicDuologue]) -> list[SubtopicText]:
    """Return the ordered subtopic duologue transcript for each subtopic within the context of the given topic and ordered list of subtopics."""
    assert subtopics_duologues
    return [
        SubtopicText(name=subtopic_duologue["subtopic"], text="\n".join(f"#S{subtopic_num}L{line_num}: [{line['speaker']}] {line['speech']} (tone: {line.get('tone')})" for line_num, line in enumerate(subtopic_duologue["duologue"], start=0))) for subtopic_num, subtopic_duologue in enumerate(subtopics_duologues, start=1)
    ]


def get_subtopics_monologue_transcripts(*, topic: str, is_from_document: bool, subtopic_monologues: list[SubtopicText], markers: bool = True) -> list[SubtopicText]:
    """Return the ordered monologue transcript for all subtopics within the context of the given topic and ordered list of subtopics.

    If markers are enabled, markers are placed at the start of each subtopic section. The disclaimer is placed at the beginning of the first section.
    If markers are disabled, they are not placed. The disclaimer is placed at the end of the last section.
    """
    assert subtopic_monologues

    mark: Callable[[str], str] = (lambda marker: marker) if markers else (lambda marker: "")
    demark: Callable[[str], str] = (lambda marker: "") if markers else (lambda marker: marker)

    process_subtopic_name: Callable[[str], str] = (lambda subtopic_name: subtopic_name.replace(".", ":", 1)) if markers else (lambda subtopic_name: subtopic_name.partition(". ")[2])
    # Note: The section number is removed altogether from the subtopic name if markers are disabled. This is because the number risks not being correctly spoken in an intended foreign language, especially so for non-Latin languages.

    for subtopic_monologue in subtopic_monologues:
        assert _NUMBERED_SUBTOPIC_PATTERN.match(subtopic_monologue["name"]), subtopic_monologue["name"]
    subtopics_monologue_transcripts = [SubtopicText(name=s["name"], text=f"{mark('Section ')}{process_subtopic_name(s['name'])}:\n\n{s['text']}") for s in subtopic_monologues]

    tts_disclaimer = TTS_DISCLAIMER_W_DOC if is_from_document else TTS_DISCLAIMER_WO_DOC
    subtopics_monologue_transcripts[0]["text"] = f"{topic}:\n\n{mark(f'{tts_disclaimer}\n\n')}{subtopics_monologue_transcripts[0]['text']}"
    subtopics_monologue_transcripts[-1]["text"] = f"{subtopics_monologue_transcripts[-1]['text']}{demark(f'\n\n{tts_disclaimer}')}"

    return subtopics_monologue_transcripts
