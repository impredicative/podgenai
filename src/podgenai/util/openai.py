import os
from pathlib import Path
from typing import Optional

import openai
import pathvalidate

import podgenai.exceptions
from podgenai.config import PACKAGE_NAME
from podgenai.util.dotenv_ import load_dotenv
from podgenai.util.binascii import hasher

load_dotenv()

ChatCompletion = openai.types.chat.chat_completion.ChatCompletion
OpenAI = openai.OpenAI

MAX_TTS_INPUT_LEN = 4096
MODELS = {
    "text": ["gpt-4o-2024-11-20", "gpt-4.1-2025-04-14", "gpt-5-2025-08-07", "gpt-5-chat-latest"][3],  # Ref: https://platform.openai.com/docs/models
    # Notes:
    #   As of 2025-08, gpt-5-chat-latest is experimentally used, mostly approximating gpt-4.1 in behavior.
    #   As of 2025-08, gpt-5-2025-08-07 is not used because it was observed to be impractically slow and verbose, although it was detailed.
    #   As of 2025-06, gpt-4.1-2025-04-14 is used because it is less likely to reject broad valid topics than gpt-4o-2024-11-20.
    #   As of 2024-11, gpt-4o-2024-11-20 is used because it seems to be even better at instruction-following than gpt-4o-2024-08-06.
    #   As of 2024-09, gpt-4o-2024-08-06 is used because it has information about newer topics that the older gpt-4-0125-preview model does not.
    #   As of 2024-05, gpt-4o-2024-05-13 is not used because it was observed to hallucinate significantly, whereas gpt-4-0125-preview doesn't.
    #   As of 2024-04, gpt-4-turbo-2024-04-09 is not used because it was observed to produce slightly lesser content than gpt-4-0125-preview.
    "tts": "tts-1",  # Note: tts-1-hd is twice as expensive, and has a more limited concurrent usage quota resulting in openai.RateLimitError, thereby making it undesirable.
}
TTS_VOICE_MAP = {  # Note: Before adding any name, ensure that *all* names are still selectable in practice by testing various topics.
    "analytical-male": "alloy",
    "elegant-female": "sage",
    "emotive-male": "echo",
    "expository-male": "ash",
    "informative-male": "onyx",
    "serene-female": "nova",
}  # Ref: https://platform.openai.com/docs/guides/text-to-speech#voice-options

EXTRA_TEXT_MODEL_PREFIX_KWARGS = {
    "gpt-4o-": {"max_completion_tokens": 16_384, "temperature": 0.7},
    "gpt-4.1-": {"max_completion_tokens": 32_768, "temperature": 0.7},
    "gpt-5-": {"max_completion_tokens": 128_000},  # Note: Temperature is not supported.
    "gpt-5-chat-": {"max_completion_tokens": 16_384},  # Note: Prefix has order dependency.
}
UNSUPPORTED_TEXT_MODEL_PREFIX_KWARGS = {
    "gpt-4o-": ("reasoning_effort", "verbosity"),
    "gpt-4.1-": ("reasoning_effort", "verbosity"),
    "gpt-5-": ("temperature",),
    "gpt-5-chat-": ("reasoning_effort", "verbosity"),
}
extra_text_model_kwargs = {kw: v for prefix, kws in EXTRA_TEXT_MODEL_PREFIX_KWARGS.items() if MODELS["text"].startswith(prefix) for kw, v in kws.items()}
unsupported_text_model_kwargs = {kw for prefix, kws in UNSUPPORTED_TEXT_MODEL_PREFIX_KWARGS.items() if MODELS["text"].startswith(prefix) for kw in kws}


def ensure_openai_key() -> None:
    """Raise `EnvError` if the environment variable OPENAI_API_KEY is unavailable."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise podgenai.exceptions.EnvError("The environment variable OPENAI_API_KEY is unavailable. It can optionally be defined in an .env file.")


def get_openai_client() -> OpenAI:
    """Return the OpenAI client."""
    return OpenAI()


def get_completion(prompt: str, *, client: Optional[OpenAI] = None, **kwargs) -> ChatCompletion:
    """Return the completion for the given prompt.

    Additional keyword arguments are forwarded to the OpenAI API client's `chat.completions.create` method.
    """
    if not client:
        client = get_openai_client()
    # print(f"Requesting completion for prompt of length {len(prompt)}.")

    model = MODELS["text"]
    completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], safety_identifier=PACKAGE_NAME, **kwargs)  #  Ref: https://platform.openai.com/docs/api-reference/chat/create

    if completion.usage and completion.usage.prompt_tokens_details and ((num_cached_prompt_tokens := completion.usage.prompt_tokens_details.cached_tokens) > 0):
        num_prompt_tokens = completion.usage.prompt_tokens
        pct_cached_prompt_tokens = num_cached_prompt_tokens / num_prompt_tokens
        print(f"Completion for prompt of {num_prompt_tokens} tokens used {num_cached_prompt_tokens} ({pct_cached_prompt_tokens:.0%}) cached input tokens.")

    return completion


def get_content(prompt: str, *, client: Optional[OpenAI] = None, completion: Optional[ChatCompletion] = None, **kwargs) -> str:
    """Return the content for the given prompt.

    Additional keyword arguments are forwarded to `get_completion`.
    """
    if not completion:
        completion = get_completion(prompt, client=client, **kwargs)
    content = completion.choices[0].message.content
    content = content.strip()
    assert content
    return content


def get_cached_content(prompt: str, *, read_cache: bool = True, cache_key_prefix: str, cache_path: Path, **kwargs) -> str:
    """Return the content for the given prompt using the disk cache if available, otherwise normally.

    Params:
    * `read_cache`: If `True`, the disk cache is read if available. If `False`, the disk cache is not read, and it will be written or overwritten.
    * `cache_key_prefix`: Friendly identifying name of request, used in filename in cache directory. Deduplication by prompt is done by this function; it does not have to be done externally.
    * `cache_path`: Cache directory.

    Additional keyword arguments, if valid for the model, are forwarded to `get_content` along with model's default keyword arguments.
    """
    cache_key_prefix = cache_key_prefix.strip()
    assert cache_key_prefix
    assert cache_path.is_dir()

    sanitized_cache_key_prefix = pathvalidate.sanitize_filename(cache_key_prefix, platform="auto")
    assert sanitized_cache_key_prefix
    cache_key = f"{sanitized_cache_key_prefix} ({MODELS['text']}) [{hasher(prompt)}].txt"
    cache_file_path = cache_path / cache_key
    pathvalidate.validate_filepath(cache_file_path, platform="auto")

    if read_cache and cache_file_path.exists():
        assert cache_file_path.is_file()
        content = cache_file_path.read_text().rstrip()  # rstrip is used in case the file is manually modified in an editor which adds a trailing newline.
        print(f"Read completion from disk for: {cache_key_prefix}")
    else:
        kwargs = {k: v for k, v in kwargs.items() if k not in unsupported_text_model_kwargs}
        kwargs = {**extra_text_model_kwargs, **kwargs}  # Note: Order of inclusion is relevant.
        kwargs_str = (" with " + " ".join(f"{k}={v}" for k, v in kwargs.items())) if kwargs else ""
        print(f"Requesting completion{kwargs_str} for: {cache_key_prefix}")
        content = get_content(prompt, **kwargs)
        print(f"Received completion{kwargs_str} for: {cache_key_prefix}")
        cache_file_path.write_text(content)

    assert content == content.rstrip()
    return content


def write_speech_audio(text: str, path: Path, *, voice: str = next(iter(TTS_VOICE_MAP)), client: Optional[OpenAI] = None) -> None:
    """Write the speech audio file for the given prompt to the given file path.

    The prompt must not be longer than 4096 characters, as this is the maximum supported length by the client.

    `voice` can be one of the keys or values in TTS_VOICE_MAP, or one of the other supported voices.
    """
    assert path.suffix == ".mp3"
    if not client:
        client = get_openai_client()

    mapped_voice = TTS_VOICE_MAP.get(voice, voice)
    voice_str = voice if (voice == mapped_voice) else f"{voice} ({mapped_voice})"

    print(f"Requesting speech audio in {voice_str} voice for: {path.stem}")
    response = client.audio.speech.create(model=MODELS["tts"], voice=mapped_voice, input=text)
    # relative_path = path.relative_to(Path.cwd())
    # print(f"Writing speech to: {relative_path}")
    response.stream_to_file(path)
    assert path.exists(), path
    # print(f"Wrote speech to: {relative_path}")
    print(f"Received speech audio in {voice_str} voice for: {path.stem}")


def ensure_speech_audio(text: str, path: Path, **kwargs) -> None:
    """Ensure the speech audio file for the given text to the given file path.

    Additional keyword arguments are forwarded to `write_speech`.
    """

    if path.exists():
        assert path.is_file()
        print(f"Speech audio file exists on disk for: {path.stem}")
        return
    write_speech_audio(text, path=path, **kwargs)
