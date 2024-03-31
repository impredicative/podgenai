from typing import Optional

from podgenai.config import PROMPTS
from podgenai.util.openai import get_cached_content, TTS_VOICE_MAP
from podgenai.util.sys import print_error


def get_voice(topic: str) -> str:
    """Return the suggested voice for the given topic."""
    prompt = PROMPTS['select_voice'].format(topic=topic)
    raw_voice = get_cached_content(prompt)
    voice = raw_voice.rstrip('.').lower()
    assert (voice in TTS_VOICE_MAP), ({'topic': topic, 'raw_voice': raw_voice, 'voice': voice, 'TTS_VOICE_MAP': TTS_VOICE_MAP})
    return voice
