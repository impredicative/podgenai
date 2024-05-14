import os
from pathlib import Path
from typing import Optional

import dotenv
import openai
import pathvalidate

import podgenai.exceptions
from podgenai.config import PROMPTS
from podgenai.util.binascii import hasher
from podgenai.util.sys import print_warning

dotenv.load_dotenv()

ChatCompletion = openai.types.chat.chat_completion.ChatCompletion
OpenAI = openai.OpenAI

MAX_TTS_INPUT_LEN = 4096
MODELS = {
    "text": "gpt-4-0125-preview",
    # Notes:
    #   As of 2024-05, gpt-4o (gpt-4o-2024-05-13) is not used because it was observed to hallucinate significantly, whereas gpt-4-turbo-preview (gpt-4-0125-preview) doesn't.
    #   As of 2024-04, gpt-4-turbo (gpt-4-turbo-2024-04-09) is not used because it was observed to produce slightly lesser content than gpt-4-turbo-preview (gpt-4-0125-preview).
    #   gpt-4 is not used because it is much older in its training data.
    "tts": "tts-1",  # Note: tts-1-hd is twice as expensive, and has a more limited concurrent usage quota resulting in openai.RateLimitError, thereby making it undesirable.
}
TTS_VOICE_MAP = {"default": "alloy", "neutral": "alloy", "female": "nova", "male": "onyx", "emotive": "echo"}  # Note: An unsolicited 'neutral' response has been observed, and is therefore supported.


def ensure_openai_key() -> None:
    """Raise `EnvError` if the environment variable OPENAI_API_KEY is unavailable."""
    if not os.environ.get("OPENAI_API_KEY"):
        raise podgenai.exceptions.EnvError("The environment variable OPENAI_API_KEY is unavailable. It can optionally be defined in an .env file.")


def get_openai_client() -> OpenAI:
    """Return the OpenAI client."""
    return OpenAI()


def get_completion(prompt: str, *, client: Optional[OpenAI] = None) -> ChatCompletion:
    """Return the completion for the given prompt."""
    if not client:
        client = get_openai_client()
    # print(f"Requesting completion for prompt of length {len(prompt)}.")
    completion = client.chat.completions.create(model=MODELS["text"], messages=[{"role": "user", "content": prompt}])
    # Note: Specifying max_tokens=4096 with gpt-4-turbo-preview did not benefit in increasing output length, and a higher value is disallowed. Ref: https://platform.openai.com/docs/api-reference/chat/create
    return completion


def get_multipart_messages(prompt: str, *, max_completions: int = 10, client: Optional[OpenAI] = None, update_prompt: bool = False, continuation: str = PROMPTS["continuation_next"]) -> list[dict]:
    """Return the multipart completion messages for the given initial prompt.

    After the initial completion, continuation prompts are subsequently given, either until the assistant is done, or until a maximum of `max_completions` are received, whichever is first.

    If `update_prompt` is True, the initial prompt is appended a default note that continuation prompts will subsequently be sent.
    If `update_prompt` is False, the initial prompt can be provided with an included continuation note.

    If `continuation` is specified, it is used iteratively as the continuation prompt, otherwise a default continuation prompt is used.
    """
    if update_prompt:
        prompt = prompt + "\n\n" + PROMPTS["continuation_first"]
    endings = ("Done", "Done.", "done", "done.")

    if not client:
        client = get_openai_client()

    messages = [{"role": "user", "content": prompt}]
    for completion_num in range(1, max_completions + 1):
        # print(f"Requesting completion {completion_num} for initial prompt of length {len(prompt)}.")
        completion = client.chat.completions.create(model=MODELS["text"], messages=messages)
        content = get_content(prompt="", completion=completion)
        messages.append({"role": "assistant", "content": content})

        if content in endings:
            print(f"Completion {completion_num} is an ending.")
            return messages
        else:
            for ending in endings:
                if content.endswith((f" {ending}", f"\n{ending}")):
                    print(f"Completion {completion_num} has an ending.")
                    return messages

        if completion_num == max_completions:
            print_warning(f"The quota of a maximum of {max_completions} completions is exhausted for initial prompt of length {len(prompt)}.")
            return messages

        messages.append({"role": "user", "content": continuation})

    assert False


def get_content(prompt: str, *, client: Optional[OpenAI] = None, completion: Optional[ChatCompletion] = None) -> str:
    """Return the content for the given prompt."""
    if not completion:
        completion = get_completion(prompt, client=client)
    content = completion.choices[0].message.content
    content = content.strip()
    assert content
    return content


def get_multipart_content(prompt: str, **kwargs) -> str:
    """Return the multipart completion content for the given initial prompt.

    Additional keyword arguments are forwarded to `get_multipart_messages`.

    The completions are joined using paragraph breaks (double line breaks).
    """
    endings = ("Done", "Done.", "done", "done.")
    messages = get_multipart_messages(prompt, **kwargs)

    completions = []
    for message_count, message in enumerate(messages, start=1):
        if message["role"] != "assistant":
            continue
        completion = message["content"]
        assert completion == completion.strip()
        if completion in endings:
            assert message_count == len(messages), {"prompt": prompt, "messages": messages, "message_count": message_count, "completion": completion}
            break
        for ending in endings:
            if completion.endswith((f" {ending}", f"\n{ending}")):
                completion = completion.removesuffix(ending).rstrip()
                break
        completions.append(completion)

    return "\n\n".join(completions).strip()


def get_cached_content(prompt: str, *, strategy: str = "oneshot", read_cache: bool = True, cache_key_prefix: str, cache_path: Path, **kwargs) -> str:
    """Return the content for the given prompt using the disk cache if available, otherwise normally.

    Params:
    * `strategy`:
        If `strategy` is 'oneshot', the assistant is requested only one output, which is usually sufficient.
        If `strategy` is 'multishot', the assistant is permitted multiple outputs up to a limit.
    * `read_cache`: If `True`, the disk cache is read if available. If `False`, the disk cache is not read, and it will be written or overwritten.
    * `cache_key_prefix`: Friendly identifying name of request, used in filename in cache directory. Deduplication by prompt is done by this function; it does not have to be done externally.
    * `cache_path`: Cache directory.

    Additional keyword arguments are forwarded to the respective underlying function, namely `get_content` for 'oneshot', and `get_multipart_content` for 'multishot'.
    """
    cache_key_prefix = cache_key_prefix.strip()
    assert cache_key_prefix
    assert cache_path.is_dir()

    sanitized_cache_key_prefix = pathvalidate.sanitize_filename(cache_key_prefix, platform="auto")
    assert sanitized_cache_key_prefix
    cache_key = f"{sanitized_cache_key_prefix} ({strategy}) [{hasher(prompt)}].txt"
    cache_file_path = cache_path / cache_key
    pathvalidate.validate_filepath(cache_file_path, platform="auto")

    if read_cache and cache_file_path.exists():
        assert cache_file_path.is_file()
        content = cache_file_path.read_text().rstrip()  # rstrip is used in case the file is manually modified in an editor which adds a trailing newline.
        print(f"Read completion from disk for: {cache_key_prefix}")
    else:
        content_getter = {"oneshot": get_content, "multishot": get_multipart_content}[strategy]
        print(f"Requesting completion for: {cache_key_prefix}")
        content = content_getter(prompt, **kwargs)
        print(f"Received completion for: {cache_key_prefix}")
        cache_file_path.write_text(content)

    assert content == content.rstrip()
    return content


def write_speech_audio(text: str, path: Path, *, voice: str = "default", client: Optional[OpenAI] = None) -> None:
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
