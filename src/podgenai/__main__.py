def get_topic() -> str:
    topic = input('Specify the topic for which to generate a podcast: ')
    topic = topic.strip()
    if len(topic) < 2:
        raise ValueError('Invalid topic.')
    return topic


def main() -> None:
    topic = get_topic()
    print(f'Generating podcast on: {topic}')


if __name__ == "__main__":
    main()
