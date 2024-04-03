from typing import Optional

from podgenai.config import PROMPTS
from podgenai.util.openai import get_cached_content
from podgenai.util.pathvalidate import get_topic_work_path
from podgenai.util.sys import print_error


def is_subtopics_list_valid(subtopics: list[str]) -> bool:
    """Return true if the subtopics are structurally valid, otherwise false.

    A validation error is printed if a subtopic is invalid.
    """
    seen = set()
    for num, subtopic in enumerate(subtopics, start=1):
        expected_num_prefix = f'{num}. '
        if subtopic != subtopic.strip():
            print_error(f'Subtopic {num} is invalid because it has leading or trailing whitespace: {subtopic!r}')
            return False
        if not subtopic.startswith(expected_num_prefix):
            print_error(f'Subtopic {num} is invalid because it is not numbered correctly: {subtopic}')
            return False
        subtopic_name = subtopic.removeprefix(expected_num_prefix).strip()
        if not subtopic_name:
            print_error(f'Subtopic {num} is invalid because it has no value: {subtopic}')
            return False
        if subtopic_name in seen:
            print_error(f'Subtopic {num} is invalid because it is a duplicate: {subtopic}')
            return False
    return True


def list_subtopics(topic: str) -> Optional[list[str]]:
    """Get the list of subtopics for the given topic."""
    prompt_name = 'list_subtopics'
    prompt = PROMPTS[prompt_name].format(topic=topic)
    subtopics = get_cached_content(prompt, cache_key_prefix=f'0. {prompt_name}', cache_path=get_topic_work_path(topic))
    assert subtopics, subtopics
    if subtopics.lower() in ('none', 'none.'):
        print_error(f'No subtopics exist for topic: {topic}')
        return
    subtopics = [s.strip() for s in subtopics.splitlines() if s]
    if not is_subtopics_list_valid(subtopics):
        print_error(f'Invalid subtopic exists for topic: {topic}')
        return
    return subtopics


def get_subtopic(*, topic: str, subtopics: list[str], subtopic: str, strategy: str = 'oneshot') -> str:
    """Get the full text for a given subtopic within the context of the given topic and list of subtopics.


    """
    assert subtopic[0].isdigit()  # Is numbered.
    common_kwargs = {'strategy': strategy, 'cache_key_prefix': subtopic, 'cache_path': get_topic_work_path(topic)}
    match strategy:
        case 'oneshot':
            prompt = PROMPTS['generate_subtopic'].format(optional_continuation='', topic=topic, subtopics='\n'.join(subtopics), numbered_subtopic=subtopic)
            subtopic = get_cached_content(prompt, **common_kwargs)
        case 'multishot':  # Observed to never really benefit or produce longer content relative to oneshot.
            prompt = PROMPTS['generate_subtopic'].format(optional_continuation='\n\n' + PROMPTS['continuation_first'], topic=topic, subtopics='\n'.join(subtopics), numbered_subtopic=subtopic)
            subtopic = get_cached_content(prompt, **common_kwargs, max_completions=5, update_prompt=False)
        case _:
            assert False, strategy
    return subtopic.rstrip()
