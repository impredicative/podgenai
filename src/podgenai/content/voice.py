import re

from podgenai.config import PROMPTS
from podgenai.util.openai import get_cached_content, TTS_VOICE_MAP
from podgenai.work import get_topic_work_path


_JOINT_PATTERN = re.compile(r"(?P<key>[\w-]+)\s+\((?P<value>[^)]+)\)")


def get_voice(topic: str, max_attempts: int = 3) -> str:
    """Return the suggested voice for the given topic.

    Params:
    * `max_attempts`: If greater than 1, and if the first attempt obtains an invalid voice, subsequent attempt(s) will be made. Only the first attempt tries to read from the disk cache.
    """
    # Note: More than a single attempt is necessary because an invalid value such as "emale" has at times been observed in the first attempt.
    prompt_name = "select_voice"
    prompt = PROMPTS[prompt_name].format(topic=topic)

    for num_attempt in range(1, max_attempts + 1):
        raw_voice = get_cached_content(prompt, read_cache=num_attempt == 1, cache_key_prefix=f"0. {prompt_name}", cache_path=get_topic_work_path(topic), reasoning_effort="minimal", verbosity="low")
        voice = raw_voice.strip().rstrip(".").lower()
        if voice in TTS_VOICE_MAP:
            break
        if (voice in TTS_VOICE_MAP.values()) and (voice := next(key for key, value in TTS_VOICE_MAP.items() if value == voice)):
            break
        if (match := _JOINT_PATTERN.fullmatch(voice)) and ((match_key := match.group("key")) in TTS_VOICE_MAP) and (match.group("value") == TTS_VOICE_MAP[match_key]):
            voice = match_key
            break

    assert voice in TTS_VOICE_MAP, {"topic": topic, "raw_voice": raw_voice, "voice": voice, "TTS_VOICE_MAP": TTS_VOICE_MAP}
    return voice
