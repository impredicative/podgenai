import datetime
import os
from typing import Optional

import dotenv
import openai

from podgenai.config import DISKCACHE
from podgenai.util.sys import print_error


dotenv.load_dotenv()

ChatCompletion = openai.types.chat.chat_completion.ChatCompletion
OpenAI = openai.OpenAI

MODEL = "gpt-4-turbo-preview"  # Note: gpt-4 is not used because it is much older in its training data.


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
    completion = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
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
