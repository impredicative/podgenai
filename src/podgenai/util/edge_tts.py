from pathlib import Path

import edge_tts

from podgenai.util.sys import print_warning
from podgenai.util.threading import exclusive_print, limit_concurrency

_TTS_MAX_CONCURRENCY: int = 1
TTS_CHUNK_BYTES_CAPACITY: int = 4096
TTS_VOICE_MAP: dict[str, str] = {
    "modern-multilingual-female": "en-US-AvaMultilingualNeural",
    "modern-multilingual-male": "en-US-AndrewMultilingualNeural",
    "professional-multilingual-female": "de-DE-SeraphinaMultilingualNeural",
    "professional-multilingual-male": "de-DE-FlorianMultilingualNeural",
}


@limit_concurrency(_TTS_MAX_CONCURRENCY)
def write_speech_audio(*, text: str, path: str | Path, voice: str) -> None:
    """Write the speech audio file for the given text to the given file path.

    Params:
    * `text`: The text to be converted to speech.
    It is advised that this be less than `TTS_CHUNK_BYTES_CAPACITY` bytes in length. If it is larger, `edge_tts` will split it into chunks, although not necessarily at preferred boundaries.
    It is advised that the text be split by the caller into compatible chunks at preferred boundaries.

    * `path`: The file path where the speech audio will be saved.
    * `voice`: The EdgeTTS voice ShortName to use for the speech synthesis.
    """
    if isinstance(path, str):
        path = Path(path)
    assert path.suffix == ".mp3"
    path.parent.mkdir(parents=True, exist_ok=True)  # Note: This is necessary for duologue subtopic directories.

    text_len_bytes = len(text.encode("utf-8"))
    if text_len_bytes > TTS_CHUNK_BYTES_CAPACITY:
        print_warning(f"EdgeTTS text of {text_len_bytes:,} bytes exceeds the advised limit of {TTS_CHUNK_BYTES_CAPACITY:,} bytes and will be split by EdgeTTS into chunks.")

    exclusive_print(f"Requesting EdgeTTS speech audio in {voice} voice for: {path.stem}")
    communicate = edge_tts.Communicate(text, voice)
    communicate.save_sync(str(path))
    assert path.exists(), path
    exclusive_print(f"Received EdgeTTS speech audio in {voice} voice for: {path.stem}")


def ensure_speech_audio(*, text: str, path: Path, voice: str) -> None:
    """Ensure the speech audio file at the given file path."""

    if path.exists():
        assert path.is_file()
        exclusive_print(f"EdgeTTS speech audio file exists on disk for: {path.stem}")
        return
    write_speech_audio(text=text, path=path, voice=voice)
