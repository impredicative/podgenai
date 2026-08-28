import os
from pathlib import Path

import openai
import pathvalidate
from openai.types.chat import ChatCompletion

import podgenai.exceptions
from podgenai.config import PACKAGE_NAME
from podgenai.util.binascii import hasher
from podgenai.util.dotenv_ import load_dotenv
from podgenai.util.threading import safe_print

load_dotenv()

OpenAI = openai.OpenAI

MODELS = {
    "text": [
        "chat-latest",  # Has a small input context window of 400K tokens which could be insufficient for a source document input.
        "gpt-5.6-sol",  # Has a large input context window of 1,050K tokens which is safer for a large source document input.
    ][-1],  # Ref: https://platform.openai.com/docs/models
    "tts": [  # Demo: https://platform.openai.com/audio/tts
        "tts-1",  # Note: tts-1-hd is twice as expensive, and was observed to have a more limited concurrent usage quota resulting in openai.RateLimitError.
        "gpt-4o-mini-tts-2025-12-15",  # Ref: https://developers.openai.com/api/docs/models/gpt-4o-mini-tts.
    ][-1],
}

if MODELS["tts"] == "tts-1":
    TTS_VOICE_MAP = {  # Note: Before adding any name, ensure that *all* names are still selectable in practice by testing various topics.
        "analytical-male": "alloy",
        "elegant-female": "sage",
        "emotive-male": "echo",
        "expository-male": "ash",
        "informative-male": "onyx",
        "serene-female": "nova",
    }  # Ref: https://platform.openai.com/docs/guides/text-to-speech#voice-options
else:
    # Note: OpenAI recommends only marin and cedar for the best quality. Ref: https://platform.openai.com/docs/guides/text-to-speech#voice-options
    TTS_VOICE_MAP = {
        "modern-female": "marin",
        "modern-male": "cedar",
    }

EXTRA_TEXT_MODEL_PREFIX_KWARGS = {
    "gpt-5.6-": {"max_completion_tokens": 128_000, "reasoning_effort": "none"},
    "chat-": {"max_completion_tokens": 128_000},
}
UNSUPPORTED_TEXT_MODEL_PREFIX_KWARGS = {
    "chat-": ("temperature", "reasoning_effort"),
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


def get_completion(prompt: str, *, client: OpenAI | None = None, **kwargs) -> ChatCompletion:
    """Return the completion for the given prompt.

    Additional keyword arguments are forwarded to the OpenAI API client's `chat.completions.create` method.
    """
    if not client:
        client = get_openai_client()
    # safe_print(f"Requesting completion for prompt of length {len(prompt)}.")

    model = MODELS["text"]
    completion = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], safety_identifier=PACKAGE_NAME, **kwargs)  #  Ref: https://platform.openai.com/docs/api-reference/chat/create

    if completion.usage and completion.usage.prompt_tokens_details and ((num_cached_prompt_tokens := completion.usage.prompt_tokens_details.cached_tokens) > 0):
        num_prompt_tokens = completion.usage.prompt_tokens
        pct_cached_prompt_tokens = num_cached_prompt_tokens / num_prompt_tokens
        safe_print(f"Completion for prompt of {num_prompt_tokens} tokens used {num_cached_prompt_tokens} ({pct_cached_prompt_tokens:.0%}) cached input tokens.")

    return completion


def get_content(prompt: str, *, client: OpenAI | None = None, completion: ChatCompletion | None = None, **kwargs) -> str:
    """Return the content for the given prompt.

    Additional keyword arguments are forwarded to `get_completion`.
    """
    if not completion:
        completion = get_completion(prompt, client=client, **kwargs)
    content = completion.choices[0].message.content
    assert isinstance(content, str)
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
        safe_print(f"Read completion from disk for: {cache_key_prefix}")
    else:
        kwargs = {k: v for k, v in kwargs.items() if k not in unsupported_text_model_kwargs}
        kwargs = {**extra_text_model_kwargs, **kwargs}  # Note: Order of inclusion is relevant.
        kwargs_str = (" with " + " ".join(f"{k}={v}" for k, v in kwargs.items())) if kwargs else ""
        safe_print(f"Requesting completion{kwargs_str} for: {cache_key_prefix}")
        content = get_content(prompt, **kwargs)  # ty: ignore[invalid-argument-type]
        safe_print(f"Received completion{kwargs_str} for: {cache_key_prefix}")
        cache_file_path.write_text(content)

    assert content == content.rstrip()
    return content


def write_speech_audio(*, text: str, path: str | Path, voice: str, tone: str | None, client: OpenAI | None = None, **kwargs) -> None:
    """Write the speech audio file for the given text to the given file path.

    Params:
    * `text`: The text to be converted to speech.
    * `path`: The file path where the speech audio will be saved.
    * `voice`: The OpenAI voice to use for the speech synthesis.
    * `tone`: The tone instructions to use for the speech synthesis, if any. The `podgenai.exceptions.SpeechModelInputError` exception is raised if the model does not support it.
    * `client`: The OpenAI client to use for the request, if any.
    * `kwargs`: Additional keyword arguments are forwarded to the OpenAI client's `audio.speech.with_streaming_response.create` method.
    """
    if isinstance(path, str):
        path = Path(path)
    assert path.suffix == ".mp3"
    path.parent.mkdir(parents=True, exist_ok=True)  # Note: This is necessary for duologue subtopic directories.

    if not client:
        client = get_openai_client()

    model = MODELS["tts"]

    if tone and (model == "tts-1"):
        raise podgenai.exceptions.SpeechModelInputError(f"Speech model {model!r} does not support tone instructions for: {path.stem}")
    if tone:
        assert "instructions" not in kwargs
        kwargs["instructions"] = tone
        # safe_print(f"Using tone instructions for: {path.stem!r}: {tone}")

    safe_print(f"Requesting speech audio in {voice} voice for: {path.stem}")
    # Ref: https://developers.openai.com/api/docs/guides/text-to-speech#quickstart
    with client.audio.speech.with_streaming_response.create(model=model, voice=voice, input=text, response_format="mp3", **kwargs) as response:
        response.stream_to_file(path)
    assert path.exists(), path
    safe_print(f"Received speech audio in {voice} voice for: {path.stem}")


def ensure_speech_audio(*, text: str, path: Path, voice: str, tone: str | None) -> None:
    """Ensure the speech audio file at the given file path."""

    if path.exists():
        assert path.is_file()
        safe_print(f"Speech audio file exists on disk for: {path.stem}")
        return
    write_speech_audio(text=text, path=path, voice=voice, tone=tone)
