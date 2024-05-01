import re

from podgenai.config import PROMPTS
from podgenai.content.topic import get_topic
from podgenai.work import get_topic_work_path


def _lstrip_optional_timestamp(topic: str) -> str:
    """Return the topic after stripping any optional leading timestamp.

    Examples:
        '2024-04-23T19:31:12 Living a good life' -> 'Living a good life'
        'Living a good life' -> 'Living a good life'
    """
    pattern = r"(?:(?:\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\s+))?(?P<topic>.*)"
    match = re.fullmatch(pattern, topic)
    return match.group("topic")


def _get_denumbered_subsections(lines: list[str]) -> list[str]:
    return [line[line.find(" ") + 1 :] if line.find(".") != -1 else line for line in lines]


def get_cached_episode_description_html(topic: str, fmt: str = "html") -> str:
    topic = _lstrip_optional_timestamp(topic)
    work_path = get_topic_work_path(topic, create=False)
    if not work_path.is_dir():
        raise LookupError(f"Work path does not exist for topic: {topic}")

    subtopics_list_files = list(work_path.glob("0. list_subtopics *.txt"))
    num_subtopics_list_files = len(subtopics_list_files)
    if num_subtopics_list_files == 0:
        raise LookupError(f"No subtopic list exists for topic: {topic}")
    elif num_subtopics_list_files > 1:
        subtopics_list_files_str = "\n".join(f"\t{f}" for f in subtopics_list_files)
        raise LookupError(f"Multiple {num_subtopics_list_files} subtopic lists exist for topic: {topic}:\n{subtopics_list_files_str}")
    assert num_subtopics_list_files == 1
    subtopics_list_file = subtopics_list_files[0]
    subtopics_text = subtopics_list_file.read_text().strip()
    subtopics_list = subtopics_text.split("\n")
    assert subtopics_list

    match fmt:
        case "html":
            denumbered_subtopics_list = _get_denumbered_subsections(subtopics_list)
            subtopics_list_html = "\n".join(f"  <li>{s}</li>" for s in denumbered_subtopics_list)
            description = f"<p><strong>Sections</strong>:</p>\n<ol>\n{subtopics_list_html}\n</ol>\n<p><br></p><p><strong>Disclaimer</strong>: <em>{PROMPTS['tts_disclaimer']}</em></p>"
        case "plain" | "text" | "txt":
            description = f"Sections:\n\n{subtopics_text}"
        case "llm" | "gpt":
            description = f"{topic}\n\nSections:\n{subtopics_text}"
        case _:
            assert False, fmt

    return description


def main():
    topic = get_topic()
    description = get_cached_episode_description_html(topic)
    print(f"\n{description}")


if __name__ == "__main__":
    main()
