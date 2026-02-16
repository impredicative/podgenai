import datetime

from podgenai.util.openai import write_speech_audio

timestamp = datetime.datetime.now().isoformat(timespec="seconds").replace(":", "-")

write_speech_audio("---", path=f"./src/podgenai/audio/pause_{timestamp}.mp3", voice="cedar", instructions="Output just an empty pause with complete quietness. Do not say anything at all.")

# Remarks:
# * As per https://developers.openai.com/api/docs/guides/text-to-speech#voice-options, for best quality, the "cedar" voice is used so as to maximize the possibility of the instructions being followed.
# * Measure pause duration at https://metadataview.com/, retrying until pause duration is approximately 1 second.
# * View pause spectrum at https://www.dcode.fr/spectral-analysis