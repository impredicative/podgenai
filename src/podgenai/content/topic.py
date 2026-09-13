import podgenai.exceptions
from podgenai.util.sys import print_error


def is_topic_valid(topic: str) -> str | None:
    """Return an error message if the topic is structurally invalid, otherwise None."""
    if not isinstance(topic, str):  # Note: This happens if `-t` flag is provided without any value.
        return "Topic must be a string."
    if topic != topic.strip():
        return "Topic must not have leading or trailing whitespace."
    if len(topic) == 0:
        return "No topic was provided."
    if len(topic) < 2:
        return "Topic must be at least two characters long."
    if len(topic.splitlines()) > 1:
        return "Topic must be in a single line."
    if (topic[0] == topic[-1] == "'") or (topic[0] == topic[-1] == '"'):
        return "Topic must not be quoted."
    if topic[-1] == ":":
        return "Topic must not end in a colon."
    return None


def ensure_topic_is_valid(topic: str) -> None:
    """Raise `InputError` if the topic is structurally invalid."""
    validation_error = is_topic_valid(topic)
    if validation_error is not None:
        raise podgenai.exceptions.InputError(validation_error)


def get_topic() -> str:
    """Get topic for generation from user input."""
    topic = None
    while not topic:
        topic = input("Specify the topic: ")
        topic = topic.strip()
        validation_error = is_topic_valid(topic)
        if validation_error is not None:
            print_error(validation_error)
            topic = None
    return topic
