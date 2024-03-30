from typing import Optional

from podgenai.config import PROMPTS
from podgenai.util.openai import get_cached_content


def get_subtopics(topic: str) -> Optional[list[str]]:
    prompt = PROMPTS['list_subtopics'].format(topic=topic)
    subtopics = get_cached_content(prompt)
    if subtopics.lower() in ('none', 'none.'):
        return
    subtopics = subtopics.splitlines()
    return subtopics
