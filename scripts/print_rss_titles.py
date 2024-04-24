import io
import urllib.request
import xml.etree.ElementTree as ET

RSS_URL = "https://anchor.fm/s/f4868644/podcast/rss"


def get_url_content(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode()


def extract_episode_titles(rss_content: str) -> list[str]:
    tree = ET.parse(io.StringIO(rss_content))
    root = tree.getroot()

    episode_titles = [item.find("title").text for item in root.findall(".//item")]
    return episode_titles


def main():
    content = get_url_content(RSS_URL)
    titles = extract_episode_titles(content)
    for title in titles:
        print(title)


if __name__ == "__main__":
    main()
