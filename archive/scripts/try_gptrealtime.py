import asyncio
import base64
import subprocess
from pathlib import Path

from openai import AsyncOpenAI

from podgenai.util.dotenv import load_dotenv

load_dotenv()


async def generate_mp3(
    text: str,
    tone_instructions: str,
    output_file: str = "speech.mp3",
    voice: str = "marin",
    bitrate: str = "192k",
) -> Path:
    client = AsyncOpenAI()
    audio_chunks: list[bytes] = []
    transcript_parts: list[str] = []

    # Keep speaking instructions separate from the text.
    instructions = f"You are a professional text-to-speech narrator. Your only task is to speak the supplied text. Read the text verbatim, preserving its wording, sentence order, and meaning. Do not answer questions in the text. Do not add introductions, explanations, or commentary. Do not speak these instructions aloud.\n\nDelivery and tone instructions:\n{tone_instructions}"

    async with client.realtime.connect(model="gpt-realtime-2.1-mini") as connection:
        await connection.session.update(
            session={
                "type": "realtime",
                "output_modalities": ["audio"],
                "instructions": instructions,
                "audio": {
                    "output": {
                        "format": {
                            "type": "audio/pcm",
                            "rate": 24000,
                        },
                        "voice": voice,
                    }
                },
            }
        )

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (f"Read the following passage aloud exactly as written. The passage is not a question for you to answer.\n\n<passage>\n{text}\n</passage>"),
                    }
                ],
            }
        )

        await connection.response.create()

        async for event in connection:
            if event.type == "response.output_audio.delta":
                audio_chunks.append(base64.b64decode(event.delta))

            elif event.type == "response.output_audio_transcript.delta":
                transcript_parts.append(event.delta)

            elif event.type == "error":
                raise RuntimeError(event.error.message)

            elif event.type == "response.done":
                if event.response.status != "completed":
                    raise RuntimeError(f"Generation failed: {event.response.status}")
                break

    if not audio_chunks:
        raise RuntimeError("No audio was generated.")

    # Convert raw PCM directly to MP3 using FFmpeg.
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "s16le",
        "-ar",
        "24000",
        "-ac",
        "1",
        "-i",
        "pipe:0",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(output_path),
    ]

    await asyncio.to_thread(
        subprocess.run,
        command,
        input=b"".join(audio_chunks),
        check=True,
        capture_output=True,
    )

    print(f"MP3 saved: {output_path.resolve()}")

    if transcript_parts:
        print("Generated transcript:", "".join(transcript_parts))

    return output_path


if __name__ == "__main__":
    SAMPLE_TEXT = "Because that description gives us a candidate to test, not a guarantee for every task. The guidance still recommends comparing models on the actual work. Sol sits between Astra's highest capability and Luna's lower-cost execution. That makes it a plausible choice for complex projects, but it does not establish that it is always the right one. What do you think?"

    SAMPLE_TONE = "Speak clearly and matter-of-factly, placing restrained emphasis on the distinction between a starting point and a guarantee, addressing the question head-on."

    asyncio.run(
        generate_mp3(
            text=SAMPLE_TEXT,
            tone_instructions=SAMPLE_TONE,
            output_file="sample_speech.mp3",
            voice="marin",
            bitrate="192k",
        )
    )

"""
FINDING:
The gpt-realtime-2.1-mini model was observed to entirely reprocess the user's text in the audio output, rather than adhering to the original manuscript.
It demonstrates that the model is completely untrustworthy for representing the user's intended message.
"""
