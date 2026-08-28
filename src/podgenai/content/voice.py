import re
from typing import Literal

import podgenai.exceptions
from podgenai.config import PROMPTS
from podgenai.util.openai import TTS_VOICE_MAP, get_cached_content
from podgenai.work import get_topic_work_path

_JOINT_PATTERN = re.compile(r"(?P<key>[\w-]+)\s+\((?P<value>[^)]+)\)")


def get_monologue_voice_key(*, topic: str, max_attempts: int = 3, allowed_voice_keys: list[str] | None = None) -> str:
    """Return the suggested voice key for the given topic.

    Params:
    * `max_attempts`: If greater than 1, and if the first attempt obtains an invalid voice, subsequent attempt(s) will be made. Only the first attempt tries to read from the disk cache.
    * `allowed_voice_keys`: If given, the returned voice is restricted to one of these supported keys.
    """
    # Note: More than a single attempt has sometimes been necessary because an invalid value such as "emale" has at times been observed in the first attempt.
    prompt_name = "select_voice"
    if allowed_voice_keys is None:
        tts_voice_map = TTS_VOICE_MAP
    else:
        for voice_key in allowed_voice_keys:
            assert voice_key in TTS_VOICE_MAP, {"topic": topic, "key": voice_key, "allowed_voice_keys": allowed_voice_keys}
        tts_voice_map = {voice_key: value for voice_key, value in TTS_VOICE_MAP.items() if voice_key in allowed_voice_keys}
    voices = "\n".join(f"    {voice_key} ({value})" for voice_key, value in sorted(tts_voice_map.items()))
    prompt = PROMPTS[prompt_name].render(voices=voices, topic=topic)

    for num_attempt in range(1, max_attempts + 1):
        raw_voice = get_cached_content(prompt, read_cache=num_attempt == 1, cache_key_prefix=f"0. {prompt_name}", cache_path=get_topic_work_path(topic))
        voice = raw_voice.strip().rstrip(".").lower()
        if voice in tts_voice_map:
            break
        if (voice in tts_voice_map.values()) and (voice := next(key for key, value in tts_voice_map.items() if value == voice)):
            break
        if (match := _JOINT_PATTERN.fullmatch(voice)) and ((match_key := match.group("key")) in tts_voice_map) and (match.group("value") == tts_voice_map[match_key]):
            voice = match_key
            break
    else:
        raise podgenai.exceptions.LanguageModelOutputError(f"Failed to obtain a valid voice for topic '{topic}' after {max_attempts} attempts. Last raw voice: '{raw_voice}'.")

    assert voice in tts_voice_map, {"topic": topic, "raw_voice": raw_voice, "voice": voice, "voice_map": tts_voice_map}
    return voice


def get_voice_sex_from_voice_key(voice_key: str) -> Literal["male", "female"]:
    """Return the sex of the voice for the given voice key as either "male" or "female"."""
    assert voice_key in TTS_VOICE_MAP, {"voice_key": voice_key, "voice_map": TTS_VOICE_MAP}
    voice_sex = {voice_key.endswith("-male"): "male", voice_key.endswith("-female"): "female"}[True]
    assert voice_sex in ("male", "female"), {"voice_key": voice_key, "voice_sex": voice_sex, "voice_map": TTS_VOICE_MAP}
    return voice_sex


def get_duologue_voice_keys(*, topic: str) -> tuple[str, str]:
    """Return the suggested voice key pair for the given topic as the marker voice and the boundary voice, one of which is male and the other female.

    The marker voice also serves as the non-boundary voice.
    """
    marker_voice = get_monologue_voice_key(topic=topic)
    marker_voice_sex = get_voice_sex_from_voice_key(marker_voice)
    leftover_allowed_voice_keys = [v for v in TTS_VOICE_MAP if (v != marker_voice) and (get_voice_sex_from_voice_key(v) != marker_voice_sex)]
    num_leftover_allowed_voice_keys = len(leftover_allowed_voice_keys)

    match num_leftover_allowed_voice_keys:
        case 0:  # If this happens, it means there is no available voice of the opposite sex in TTS_VOICE_MAP.
            assert False, {"topic": topic, "marker_voice": marker_voice, "voice_map": TTS_VOICE_MAP}
        case 1:
            boundary_voice = leftover_allowed_voice_keys[0]
        case _:
            assert num_leftover_allowed_voice_keys > 1
            boundary_voice = get_monologue_voice_key(topic=topic, allowed_voice_keys=leftover_allowed_voice_keys)

    assert marker_voice in TTS_VOICE_MAP
    assert boundary_voice in TTS_VOICE_MAP
    assert marker_voice != boundary_voice
    assert marker_voice_sex != get_voice_sex_from_voice_key(boundary_voice)
    return marker_voice, boundary_voice
