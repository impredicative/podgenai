import contextlib
import io

import podgenai.exceptions
from podgenai.util.sys import print_error


def is_topic_valid(topic: str) -> bool:
    """Return true if the topic is structurally valid, otherwise false.

    A validation error is printed if the topic is false.
    """
    if not isinstance(topic, str):  # Note: This happens if `-t` flag is provided without any value.
        print_error("Topic must be a string.")
        return False
    if topic != topic.strip():
        print_error("Topic must not have leading or trailing whitespace.")
        return False
    if len(topic) == 0:
        print_error("No topic was provided.")
        return False
    if len(topic) < 2:
        print_error("Topic must be at least two characters long.")
        return False
    if len(topic.splitlines()) > 1:
        print_error("Topic must be in a single line.")
        return False
    if (topic[0] == topic[-1] == "'") or (topic[0] == topic[-1] == '"'):
        print_error("Topic must not be quoted.")
        return False
    return True


def ensure_topic_is_valid(topic: str) -> None:
    """Raise `InputError` if the topic is structurally invalid."""
    error = io.StringIO()
    with contextlib.redirect_stderr(error):
        if not is_topic_valid(topic):
            error = error.getvalue().rstrip().removeprefix("Error: ")
            raise podgenai.exceptions.InputError(error)


def get_topic() -> str:
    """Get topic for generation from user input."""
    topic = None
    while not topic:
        topic = input("Specify the topic: ")
        topic = topic.strip()
        if not is_topic_valid(topic):
            topic = None
    return topic
