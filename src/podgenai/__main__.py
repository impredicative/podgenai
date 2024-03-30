from podgenai.topic import get_topic


def main() -> None:
    topic = get_topic()
    print(f'Generating podcast on: {topic}')


if __name__ == "__main__":
    main()
