from pathlib import Path

from podgenai.podgenai import generate_podcast
from podgenai.topic import get_topic


def main() -> None:
    """Generate and write podcast to file for a user-specified topic."""
    topic = get_topic()
    print(f'Generating podcast on: {topic}')
    path = generate_podcast(topic)
    relative_path = path.relative_to(Path.cwd())
    print(f'Wrote podcast to: {relative_path}')


if __name__ == "__main__":
    main()
