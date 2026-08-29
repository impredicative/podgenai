import argparse
import re
import sys

from podgenai.config import TTS_DISCLAIMER_W_DOC, TTS_DISCLAIMER_WO_DOC
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
    assert match
    return match.group("topic")


def _get_denumbered_subsections(lines: list[str]) -> list[str]:
    return [line[line.find(" ") + 1 :] if line.find(".") != -1 else line for line in lines]


def get_cached_episode_description(topic: str, fmt: str, is_from_document: bool = False) -> str:
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
    subtopics_list = [s.strip() for s in subtopics_list if s.strip()]
    subtopics_text_stripped = "\n".join(subtopics_list)
    assert subtopics_list

    match fmt:
        case "html" | "spotify":
            tts_disclaimer = TTS_DISCLAIMER_W_DOC if is_from_document else TTS_DISCLAIMER_WO_DOC
            denumbered_subtopics_list = _get_denumbered_subsections(subtopics_list)

            if all(":" in s for s in denumbered_subtopics_list):
                reformatted_denumbered_subtopics = []
                for subtopic in denumbered_subtopics_list:
                    partitioned_subtopic = subtopic.partition(":")
                    if all(partitioned_subtopic):
                        subtopic = "<strong>" + partitioned_subtopic[0] + "</strong>: " + partitioned_subtopic[2].strip()
                    reformatted_denumbered_subtopics.append(subtopic)
                denumbered_subtopics_list = reformatted_denumbered_subtopics

            is_description_truncated = False
            indent = "  "
            while True:
                subtopics_list_html = "\n".join(f"{indent}<li>{s}</li>" for s in denumbered_subtopics_list)
                truncation_notice = f"<p><em>(Description is truncated down from {len(subtopics_list)} to {len(denumbered_subtopics_list)} sections due to a size restriction.)</em></p>\n" if is_description_truncated else ""
                description = f"<p><strong>Sections</strong>:</p>\n<ol>\n{subtopics_list_html}\n</ol>\n{truncation_notice}<p><br></p><p><strong>Disclaimer</strong>: <em>{tts_disclaimer}</em></p>"
                if len(description) <= 4000:
                    break
                else:
                    if indent:
                        indent = ""
                        continue
                    denumbered_subtopics_list.pop()
                    is_description_truncated = True
        case "plain" | "text" | "txt":
            description = f"Sections:\n\n{subtopics_text_stripped}"
        case "llm" | "chat":
            description = f"{topic}\n\nSections:\n{subtopics_text_stripped}"
        case _:
            sys.exit(f"Unsupported format: {fmt}.")

    return description


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", help="Episode topic.")
    parser.add_argument("-d", action="store_true", help="Episode was created from a document.")
    parser.add_argument("-f", default="html", help="Description format.")
    args = parser.parse_args()

    topic = args.t or get_topic()

    description = get_cached_episode_description(topic, fmt=args.f, is_from_document=args.d)
    print(f"\nHTML:\n{description}")


if __name__ == "__main__":
    main()
