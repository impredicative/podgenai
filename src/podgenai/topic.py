from podgenai.util.sys import print_error


def is_topic_valid(topic: str) -> bool:
    """Return true if the topic is structurally valid, otherwise false.

    A validation error is printed if the topic is false.
    """
    if topic != topic.strip():
        print_error('Topic must not have leading or trailing whitespace.')
        return False
    if len(topic) < 2:
        print_error('Topic must be at least two characters long.')
        return False
    if len(topic.splitlines()) > 1:
        print_error('Topic must be in a single line.')
        return False
    return True


def get_topic() -> str:
    """Get topic for podcast from user input."""
    topic = None
    while not topic:
        topic = input('Specify the topic for which to generate a podcast: ')
        topic = topic.strip()
        if not is_topic_valid(topic):
            topic = None
    return topic
