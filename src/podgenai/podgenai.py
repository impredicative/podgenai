from pathlib import Path

from podgenai.config import MAX_CONCURRENT_WORKERS, NUM_SECTIONS_MAX, NUM_SECTIONS_MIN
from podgenai.content.audio import get_output_file_path, merge_speech_paths
from podgenai.content.document import ensure_document_is_valid
from podgenai.content.subtopics import get_subtopics_duologues, get_subtopics_duologues_transcripts, get_subtopics_monologue_transcripts, get_subtopics_monologues, list_subtopics, mark_subtopics_duologues
from podgenai.content.topic import ensure_topic_is_valid
from podgenai.content.tts import ensure_speech_audio_files, get_duologue_speech_tasks, get_monologue_speech_tasks
from podgenai.content.voice import get_duologue_voice_keys, get_monologue_voice_key, get_voice_sex_from_voice_key
from podgenai.exceptions import InputError
from podgenai.util.input import get_confirmation
from podgenai.util.openai import MODELS, TTS_VOICE_MAP, ensure_openai_key
from podgenai.util.tiktoken import get_token_count
from podgenai.work import get_topic_work_path


def generate_media(topic: str, *, output_path: Path | None = None, document: str | None = None, max_sections: int | None = None, speakers: int = 2, markers: bool = True, confirm: bool = False) -> Path:
    """Return the output path after generating and writing an audiobook podcast to file for the given topic.

    Params:
    * `topic`: Topic.
    * `output_path`: Output file or directory path.
        If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined.
        If not given, the output file is written to the repo directory with an auto-determined file name.
    * `document`: Contents of a single text or markdown document to use as the exclusive source for the podcast.
        If not given, the podcast is generated from the model's internal knowledge.
    * `max_sections`: Maximum number of sections to generate. It is between 3 and 100. It is unrestricted if not given.
    * `speakers`: Number of speakers, either 1 or 2. Its default is 2.
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
    print(f"MODELS: knowledge={MODELS['knowledge']['name']}, text={MODELS['text']['name']}, tts={MODELS['tts']}")
    print(f"WORKERS: {MAX_CONCURRENT_WORKERS}")
    if max_sections is not None:
        if not (NUM_SECTIONS_MIN <= max_sections <= NUM_SECTIONS_MAX):
            raise InputError(f"Max sections is {max_sections} but it must be between {NUM_SECTIONS_MIN} and {NUM_SECTIONS_MAX}.")
        print(f"SECTIONS: ≤{max_sections}")
    if speakers not in (1, 2):
        raise InputError(f"Speakers is {speakers} but it must be either 1 or 2.")
    print(f"SPEAKERS: {speakers}")
    print(f"MARKERS: {'enabled' if markers else 'disabled'}")
    if document is not None:
        document = document.strip()
        ensure_document_is_valid(document)
    print(f"CONFIRMATIONS: {'enabled' if confirm else 'disabled'}")

    subtopics_list = list_subtopics(topic, document=document, max_sections=max_sections)  # Can commonly raise an exception, so it's done before getting voice.

    match speakers:
        case 1:
            voice_key = get_monologue_voice_key(topic=topic)
            print(f"VOICE: {voice_key} ({TTS_VOICE_MAP[voice_key]})")
        case 2:
            marker_voice_key, boundary_voice_key = get_duologue_voice_keys(topic=topic)
            non_boundary_voice_key = marker_voice_key
            print(f"VOICES: {marker_voice_key} ({TTS_VOICE_MAP[marker_voice_key]}), {boundary_voice_key} ({TTS_VOICE_MAP[boundary_voice_key]})")
            marker_voice_sex = get_voice_sex_from_voice_key(marker_voice_key)
            boundary_voice_sex = get_voice_sex_from_voice_key(boundary_voice_key)
            non_boundary_voice_sex = get_voice_sex_from_voice_key(non_boundary_voice_key)
            voice_keys_by_sex = {boundary_voice_sex: boundary_voice_key, non_boundary_voice_sex: non_boundary_voice_key}
            male_voice_key = voice_keys_by_sex["male"]
            female_voice_key = voice_keys_by_sex["female"]
        case _:
            assert False
    print(f"SUBTOPICS:\n{'\n'.join(subtopics_list)}")
    if document is not None:
        document_subtopic_model = MODELS["text"]["name"]  # Note: With the document present, the knowledge model is not used by get_subtopic_monologue due to a prohibitive cost.
        document_token_count = get_token_count(document, model=document_subtopic_model)
        cumulative_document_token_count = document_token_count * len(subtopics_list)
        print(f"DOCUMENT: {document_token_count:,} input tokens x {len(subtopics_list)} subtopics = {cumulative_document_token_count:,} input tokens ({document_subtopic_model})")

    if confirm:
        task = "monologue text generation"
        if speakers == 2:
            task += " (used subsequently for duologue)"
        get_confirmation(task)

    subtopics_monologues = get_subtopics_monologues(topic=topic, document=document, subtopics=subtopics_list)
    subtopics_monologue_transcripts = get_subtopics_monologue_transcripts(topic=topic, is_from_document=bool(document), subtopic_monologues=subtopics_monologues, markers=markers)
    assert subtopics_monologue_transcripts
    monologue = "\n\n".join(subtopic["text"] for subtopic in subtopics_monologue_transcripts)
    print(f"\nMONOLOGUE:\n{monologue}\n")
    match speakers:
        case 1:
            pass
        case 2:
            if confirm:
                get_confirmation("duologue text generation")
            subtopics_duologues = get_subtopics_duologues(topic=topic, subtopics_monologues=subtopics_monologues, boundary_voice_sex=boundary_voice_sex, non_boundary_voice_sex=non_boundary_voice_sex)  # Note: Document is not needed or used.
            mark_subtopics_duologues(topic=topic, is_from_document=bool(document), subtopics_duologues=subtopics_duologues, markers=markers, marker_voice_sex=marker_voice_sex)
            subtopics_duologue_transcripts = get_subtopics_duologues_transcripts(subtopics_duologues=subtopics_duologues)
            duologue = "\n\n".join(subtopic["text"] for subtopic in subtopics_duologue_transcripts)
            print(f"\nDUOLOGUE:\n{duologue}\n")
        case _:
            assert False

    match speakers:
        case 1:
            speech_tasks = get_monologue_speech_tasks(subtopics_monologue_transcripts=subtopics_monologue_transcripts, topic=topic, voice_key=voice_key)
        case 2:
            speech_tasks = get_duologue_speech_tasks(subtopics_duologues=subtopics_duologues, topic=topic, male_voice_key=male_voice_key, female_voice_key=female_voice_key)
    print("SPEECHES:")
    for speech_task_num, speech_task in enumerate(speech_tasks, start=1):
        print(f"{speech_task_num}: text_len={len(speech_task['text']):,} tone_len={len(speech_task['tone'] or ''):,}) pause_after={str(speech_task['pause_after']).lower()} stem={speech_task['path'].relative_to(work_path).stem!r}")

    if confirm:
        get_confirmation("speech audio generation")
    ensure_speech_audio_files(speech_tasks)

    output_path = get_output_file_path(output_path, topic=topic)
    merge_speech_paths(speech_tasks, topic=topic, output_path=output_path)
    print(f"OUTPUT: {output_path}")
    return output_path
