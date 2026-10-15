# /// script
# requires-python = ">=3.15"
# dependencies = [
#     "edge-tts>=7.3.1",
# ]
# ///

# Management commands:
# uv add --active --script ./archive/scripts/try_edgetts.py edge-tts
# uv run --active ./archive/scripts/try_edgetts.py

import asyncio

import edge_tts

from podgenai.util.semantic_text_splitter import semantic_split_by_byte_length

TEXT = "Choosing GPT-6.1 Sol is a decision about the quality a task requires, the time available to finish it, and the cost of obtaining a usable result. Those three factors belong together. A lower-priced response is not necessarily economical if it fails to complete the work. A more capable configuration is not necessarily worthwhile if its additional work does not improve the deliverable."
VOICE = ["en-US-AndrewMultilingualNeural", "en-US-AvaMultilingualNeural"][0]  # Selection: https://github.com/yaph/tts-samples/tree/main/mp3/English https://geeksta.net/tools/tts-samples/
OUTPUT_FILE = "test.mp3"


def main() -> None:
    """Main function"""

    voices = asyncio.run(edge_tts.list_voices())
    num_voices = len(voices)
    num_en_us_voices = sum(1 for voice in voices if voice["Locale"] == "en-US")
    print(f"Voices (total={num_voices}, en-US={num_en_us_voices}):")
    en_us_voices = [voice for voice in voices if voice["Locale"] == "en-US"]
    for voice_num, voice in enumerate(en_us_voices, start=1):
        print(f"{voice_num}. {voice}")

    assert VOICE in [voice["ShortName"] for voice in voices]
    chunks = semantic_split_by_byte_length(TEXT, limit=4096)  # Ref: https://github.com/rany2/edge-tts/discussions/497#discussioncomment-18910349
    for chunk_num, chunk in enumerate(chunks, start=1):
        communicate = edge_tts.Communicate(chunk, VOICE)
        communicate.save_sync(f"{OUTPUT_FILE}_{VOICE}_{chunk_num}.mp3")


if __name__ == "__main__":
    main()
