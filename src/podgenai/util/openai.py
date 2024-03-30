import os

import openai

from podgenai.util.sys import print_error


def is_openai_key_available() -> bool:
    """Return true if the OPENAI_API_KEY environment value is available, otherwise false."""
    value = os.environ.get("OPENAI_API_KEY")
    if not value:
        print_error('The environment variable OPENAI_API_KEY is unavailable. It can optionally be defined in an .env file.')
        return False
    return True


def get_openai_client():
    return openai.OpenAI()
