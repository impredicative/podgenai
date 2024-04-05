from podgenai.config import PROMPTS
from podgenai.util.openai import get_cached_content, TTS_VOICE_MAP
from podgenai.work import get_topic_work_path


def get_voice(topic: str) -> str:
    """Return the suggested voice for the given topic."""
    prompt_name = "select_voice"
    prompt = PROMPTS[prompt_name].format(topic=topic)
    raw_voice = get_cached_content(prompt, cache_key_prefix=f"0. {prompt_name}", cache_path=get_topic_work_path(topic))
    voice = raw_voice.rstrip(".").lower()
    assert voice in TTS_VOICE_MAP, {"topic": topic, "raw_voice": raw_voice, "voice": voice, "TTS_VOICE_MAP": TTS_VOICE_MAP}
    return voice
