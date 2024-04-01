from typing import Optional

from podgenai.config import PROMPTS
from podgenai.util.openai import get_cached_content
from podgenai.util.sys import print_error


def is_subtopics_list_valid(subtopics: list[str]) -> bool:
    """Return true if the subtopics are structurally valid, otherwise false.

    A validation error is printed if a subtopic is invalid.
    """
    seen = set()
    for num, subtopic in enumerate(subtopics, start=1):
        expected_num_prefix = f'{num}. '
        if not subtopic.startswith(expected_num_prefix):
            print_error(f'Subtopic {num} is invalid because it is not numbered correctly: {subtopic}')
            return False
        subtopic_text = subtopic.removeprefix(expected_num_prefix).strip()
        if not subtopic_text:
            print_error(f'Subtopic {num} is invalid because it has no value: {subtopic}')
            return False
        if subtopic_text in seen:
            print_error(f'Subtopic {num} is invalid because it is a duplicate: {subtopic}')
            return False
        return True


def list_subtopics(topic: str) -> Optional[list[str]]:
    """Get the list of subtopics for the given topic."""
    prompt = PROMPTS['list_subtopics'].format(topic=topic)
    subtopics = get_cached_content(prompt)
    assert subtopics, subtopics
    if subtopics.lower() in ('none', 'none.'):
        print_error(f'No subtopics exist for topic: {topic}')
        return
    subtopics = [s for s in subtopics.splitlines() if s]
    if not is_subtopics_list_valid(subtopics):
        print_error(f'Invalid subtopic exists for topic: {topic}')
        return
    return subtopics


def get_subtopic(*, topic: str, subtopics: list[str], subtopic: str) -> str:
    """Get the full text for a given subtopic within the context of the given topic and list of subtopics."""
    prompt = PROMPTS['generate_subtopic'].format(optional_continuation='', topic=topic, subtopics='\n'.join(subtopics), subtopic=subtopic)
    subtopic = get_cached_content(prompt)
    return subtopic
