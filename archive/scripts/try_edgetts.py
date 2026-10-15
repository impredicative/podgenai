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
VOICE = ["en-US-AndrewMultilingualNeural", "en-US-AvaMultilingualNeural"][1]  # Selection: https://github.com/yaph/tts-samples/tree/main/mp3/English https://geeksta.net/tools/tts-samples/
OUTPUT_FILE = "test.mp3"

VoiceType = dict[str, str]


def get_voices() -> list[VoiceType]:
    return asyncio.run(edge_tts.list_voices())


def print_voices(voices: list[VoiceType], *, filter_fn: callable[[VoiceType], bool] | None = None) -> None:
    num_voices = len(voices)
    if filter_fn:
        voices = [voice for voice in voices if filter_fn(voice)]
    num_filtered_voices = len(voices)
    print(f"Filtered voices (total={num_voices}, filtered={num_filtered_voices}):")
    for voice_num, voice in enumerate(voices, start=1):
        print(f"{voice_num}. {voice}")


def write_sample(voices: list[VoiceType]) -> None:
    assert VOICE in [voice["ShortName"] for voice in voices]
    chunks = semantic_split_by_byte_length(TEXT, limit=4096)  # Ref: https://github.com/rany2/edge-tts/discussions/497#discussioncomment-18910349
    for chunk_num, chunk in enumerate(chunks, start=1):
        communicate = edge_tts.Communicate(chunk, VOICE)
        communicate.save_sync(f"{OUTPUT_FILE}_{VOICE}_{chunk_num}.mp3")


if __name__ == "__main__":
    voices = get_voices()
    print_voices(voices, filter_fn=lambda voice: voice["Locale"] == "en-US")
    print_voices(voices, filter_fn=lambda voice: "Multilingual" in voice["ShortName"])
    write_sample(voices)
