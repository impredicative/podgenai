import datetime
import os
from pathlib import Path
from typing import Optional

import dotenv
import openai

from podgenai.config import DISKCACHE, PROMPTS
from podgenai.util.sys import print_error, print_warning


dotenv.load_dotenv()

ChatCompletion = openai.types.chat.chat_completion.ChatCompletion
OpenAI = openai.OpenAI

MODELS = {
    'text': "gpt-4-turbo-preview",  # Note: gpt-4 is not used because it is much older in its training data.
    'tts': "tts-1",  # TODO: Compare with tts-1-hd.
}
TTS_VOICE_MAP = {'default': 'alloy', 'male': 'onyx', 'female': 'nova'}
TTS_DISCLAIMER = 'Both the text and the audio of this podcast are AI generated, and inaccuracies or unintended content may exist.'  # Disclaimer about AI generated audio is required by OpenAI as per https://platform.openai.com/docs/guides/text-to-speech/do-i-own-the-outputted-audio-files


def is_openai_key_available() -> bool:
    """Return true if the OPENAI_API_KEY environment value is available, otherwise false."""
    value = os.environ.get("OPENAI_API_KEY")
    if not value:
        print_error('The environment variable OPENAI_API_KEY is unavailable. It can optionally be defined in an .env file.')
        return False
    return True


def get_openai_client() -> OpenAI:
    """Return the OpenAI client."""
    return OpenAI()


def get_completion(prompt: str, *, client: Optional[OpenAI] = None) -> ChatCompletion:
    """Return the completion for the given prompt."""
    if not client:
        client = get_openai_client()
    print(f'Getting completion for prompt of length {len(prompt)}.')
    completion = client.chat.completions.create(model=MODELS['text'], messages=[{"role": "user", "content": prompt}])
    return completion


def get_multipart_messages(prompt: str, *, max_completions: int = 10, client: Optional[OpenAI] = None, update_prompt: bool = False, continuation: str = PROMPTS['continuation_next']) -> list[dict]:
    """Return the multipart completion messages for the given initial prompt.

    After the initial completion, continuation prompts are subsequently given, either until the assistant is done, or until a maximum of `max_completions` are received, whichever is first.

    If `update_prompt` is True, the initial prompt is appended a default note that continuation prompts will subsequently be sent.
    If `update_prompt` is False, the initial prompt can be provided with an included continuation note.

    If `continuation` is specified, it is used iteratively as the continuation prompt, otherwise a default continuation prompt is used.
    """
    if update_prompt:
        prompt = prompt + '\n\n' + PROMPTS['continuation_first']
    endings = ('Done', 'Done.', 'done', 'done.')

    if not client:
        client = get_openai_client()

    messages = [{"role": "user", "content": prompt}]
    for completion_num in range(1, max_completions + 1):
        print(f'Getting completion {completion_num} for initial prompt of length {len(prompt)}.')
        completion = client.chat.completions.create(model=MODELS['text'], messages=messages)
        content = get_content(prompt='', completion=completion)
        messages.append({'role': 'assistant', 'content': content})

        if content in endings:
            print(f'Completion {completion_num} is an ending.')
            return messages
        else:
            for ending in endings:
                if content.endswith((f' {ending}', f'\n{ending}')):
                    print(f'Completion {completion_num} has an ending.')
                    return messages

        if completion_num == max_completions:
            print_warning(f'The quota of a maximum of {max_completions} completions is exhausted for initial prompt of length {len(prompt)}.')
            return messages

        messages.append({'role': 'user', 'content': continuation})

    assert False


def get_content(prompt: str, *, client: Optional[OpenAI] = None, completion: Optional[ChatCompletion] = None) -> str:
    """Return the content for the given prompt."""
    if not completion:
        completion = get_completion(prompt, client=client)
    content = completion.choices[0].message.content
    content = content.strip()
    assert content
    return content


@DISKCACHE.memoize(expire=datetime.timedelta(weeks=4).total_seconds(), tag='get_cached_content')
def get_cached_content(prompt: str) -> str:
    """Return the content for the given prompt using the disk cache if available, otherwise normally."""
    return get_content(prompt)


def get_multipart_content(prompt: str, **kwargs) -> str:
    """Return the multipart completion content for the given initial prompt.

    Additional keyword arguments are forwarded to `get_multipart_messages`.

    The completions are joined using paragraph breaks (double line breaks).
    """
    endings = ('Done', 'Done.', 'done', 'done.')
    messages = get_multipart_messages(prompt, **kwargs)

    completions = []
    for message_count, message in enumerate(messages, start=1):
        if message['role'] != 'assistant':
            continue
        completion = message['content']
        assert completion == completion.strip()
        if completion in endings:
            assert (message_count == len(messages)), {'prompt': prompt, 'messages': messages, 'message_count': message_count, 'completion': completion}
            break
        for ending in endings:
            if completion.endswith((f' {ending}', f'\n{ending}')):
                completion = completion.removesuffix(ending).rstrip()
                break
        completions.append(completion)

    return '\n\n'.join(completions)


@DISKCACHE.memoize(expire=datetime.timedelta(weeks=4).total_seconds(), tag='get_cached_multipart_content')
def get_cached_multipart_content(prompt: str, **kwargs) -> str:
    """Return the multipart content for the given prompt using the disk cache if available, otherwise normally.

    Additional keyword arguments are forwarded to `get_multipart_content`.
    """
    return get_multipart_content(prompt, **kwargs)


def write_speech(prompt: str, path: Path, *, voice: str = 'default', client: Optional[OpenAI] = None) -> None:  # TODO: Use disk caching.
    """Write the speech for the given prompt to the given path.

    The prompt must not be longer than 4096 characters, as this is the maximum supported length by the client.

    `voice` can be one of the keys or values in TTS_VOICE_MAP, or one of the other supported voices.
    """
    if not client:
        client = get_openai_client()

    mapped_voice = TTS_VOICE_MAP.get(voice, voice)
    voice_str = voice if (voice == mapped_voice) else f'{voice} ({mapped_voice})'

    print(f'Getting speech for input of length {len(prompt)} in {voice_str} voice.')
    response = client.audio.speech.create(model=MODELS['tts'], voice=mapped_voice, input=prompt)

    relative_path = path.relative_to(Path.cwd())
    print(f'Writing to: {relative_path}')
    response.stream_to_file(path)
    print(f'Wrote to: {relative_path}')
