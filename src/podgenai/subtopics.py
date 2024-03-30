from podgenai.util.openai import get_openai_client


def get_subtopics(topic: str) -> str:
    client = get_openai_client()
