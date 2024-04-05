import re

from podgenai.config import REPO_PATH
from podgenai import generate_media


def list_sample_topics_from_readme() -> list[str]:
    """Return the list of topics from the "Samples" section in the repository's README.md file.

    This function specifically looks for the "Samples" section in the text.
    It then identifies the markdown table within this section and extracts all entries under the
    "Name" column. The assumption is that the table is well-formed according to markdown standards
    and that the "Name" column contains markdown links with the names being the link text.

    In essence, the approach involves:
    1. Using a regular expression to locate the "Samples" section by finding the heading and
       capturing the content until the next level 2 heading or the end of the content.
    2. Extracting the portion of text that corresponds to the table under the "Samples" section.
    3. Using another regular expression to find all instances of markdown link texts in the "Name" column
       of the table. This is based on the markdown link syntax `[link text](URL)`.
    """
    readme_path = REPO_PATH / "README.md"
    readme_text = readme_path.read_text()

    # Find the section starting with "## Samples" and take the content up to the next level 2 heading
    match = re.search(r"## Samples\n(.*?)(\n## |\Z)", readme_text, re.DOTALL)
    assert match

    # Extract the table part
    samples_section = match.group(1)

    # Match all names in the "Name" column assuming they're in markdown link format [text](url)
    names = re.findall(r"\|\s*\[([^\]]+)\]", samples_section)

    # Validate names
    for name in names:
        assert name == name.strip()
    assert len(names) == len(set(names))

    return names


def generate_samples(**kwargs) -> None:
    """Generate the media for sample topics listed in the readme.

    This can be applicable as a step toward updating the samples.

    If a generation fails, all remaining topics are skipped.
    """
    topics = list_sample_topics_from_readme()
    for topic in topics:
        if not generate_media(topic, **kwargs):
            break


if __name__ == "__main__":
    generate_samples(confirm=True)
