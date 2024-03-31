import datetime
import os
from pathlib import Path
from typing import Optional

import dotenv
import openai

from podgenai.config import DISKCACHE
from podgenai.util.sys import print_error


dotenv.load_dotenv()

ChatCompletion = openai.types.chat.chat_completion.ChatCompletion
OpenAI = openai.OpenAI

MODELS = {
    'text': "gpt-4-turbo-preview",  # Note: gpt-4 is not used because it is much older in its training data.
    'tts': "tts-1",  # TODO: Compare with tts-1-hd.
}
TTS_VOICE_MAP = {'default': 'alloy', 'male': 'onyx', 'female': 'nova'}
TTS_DISCLAIMER = 'Both the text and the audio of this podcast are AI generated, and inaccuracies may exist.'  # Required by OpenAI as per https://platform.openai.com/docs/guides/text-to-speech/do-i-own-the-outputted-audio-files


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


def get_content(prompt: str, *, client: Optional[OpenAI] = None, completion: Optional[ChatCompletion] = None) -> str:
    """Return the content for the given prompt."""
    if not completion:
        completion = get_completion(prompt, client=client)
    content = completion.choices[0].message.content
    assert (content == content.strip()), content
    return content


@DISKCACHE.memoize(expire=datetime.timedelta(weeks=4).total_seconds(), tag='get_cached_content')
def get_cached_content(prompt: str) -> str:
    return get_content(prompt)


def write_speech(prompt: str, path: Path, *, voice: str = 'default', client: Optional[OpenAI] = None) -> None:  # TODO: Use disk caching.
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
