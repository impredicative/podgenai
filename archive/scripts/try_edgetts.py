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

TEXTS = {
    "English": "Choosing GPT-6.1 Sol is a decision about the quality a task requires, the time available to finish it, and the cost of obtaining a usable result. Those three factors belong together. A lower-priced response is not necessarily economical if it fails to complete the work. A more capable configuration is not necessarily worthwhile if its additional work does not improve the deliverable.",
    "French": "Choisir GPT-6.1 Sol est une décision concernant la qualité qu'une tâche exige, le temps disponible pour la terminer et le coût d'obtention d'un résultat utilisable. Ces trois facteurs vont ensemble. Une réponse moins chère n'est pas nécessairement économique si elle ne parvient pas à accomplir le travail. Une configuration plus performante n'est pas nécessairement intéressante si son travail supplémentaire n'améliore pas le livrable.",
    "Hindi": "GPT-6.1 Sol को चुनना इस बात के बारे में एक निर्णय है कि किसी कार्य के लिए आवश्यक गुणवत्ता, इसे पूरा करने के लिए उपलब्ध समय, और एक उपयोगी परिणाम प्राप्त करने की लागत। ये तीनों कारक एक साथ आते हैं। यदि यह काम पूरा करने में विफल रहता है, तो कम कीमत वाला उत्तर जरूरी नहीं कि आर्थिक हो। यदि अतिरिक्त काम डिलीवर करने योग्य परिणाम में सुधार नहीं करता है, तो अधिक सक्षम कॉन्फ़िगरेशन जरूरी नहीं कि सार्थक हो।",
    "Arabic": "اختيار GPT-6.1 Sol هو قرار يتعلق بجودة المهمة المطلوبة، والوقت المتاح لإنهائها، وتكلفة الحصول على نتيجة قابلة للاستخدام. هذه العوامل الثلاثة مرتبطة ببعضها البعض. الرد الأرخص ليس بالضرورة اقتصاديًا إذا فشل في إتمام العمل. التكوين الأكثر قدرة ليس بالضرورة مجديًا إذا لم يحسن العمل الإضافي الناتج النهائي.",
}
VOICES = [  # Note: Only multilingual voices are listed in an attempt to auto-detect and support multiple languages.
    # "en-AU-WilliamMultilingualNeural",  # NOK
    "en-US-AndrewMultilingualNeural",  # OK
    "en-US-AvaMultilingualNeural",  # OK
    # "en-US-BrianMultilingualNeural",  # NOK
    # "en-US-EmmaMultilingualNeural",  # NOK
    # "fr-FR-VivienneMultilingualNeural",  # NOK
    # "fr-FR-RemyMultilingualNeural", # Inconclusive
    "de-DE-SeraphinaMultilingualNeural",  # OK
    "de-DE-FlorianMultilingualNeural",  # OK
    # "it-IT-GiuseppeMultilingualNeural", # Inconclusive
    # "ko-KR-HyunsuMultilingualNeural",  # NOK
    # "pt-BR-ThalitaMultilingualNeural",  # NOK
]  # Selection: https://github.com/yaph/tts-samples/tree/main/mp3/English https://geeksta.net/tools/tts-samples/
OUTPUT_FILE_PREFIX = "sample"

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


def write_sample(*, lang: str, text: str, voice: str) -> None:
    chunks = semantic_split_by_byte_length(text, limit=4096)  # Ref: https://github.com/rany2/edge-tts/discussions/497#discussioncomment-18910349
    for chunk_num, chunk in enumerate(chunks, start=1):
        print(f"Writing chunk {chunk_num} for language {lang} in voice {voice}.")
        communicate = edge_tts.Communicate(chunk, voice)
        communicate.save_sync(f"{OUTPUT_FILE_PREFIX}_{lang}_{voice}_{chunk_num}.mp3")
        # print(f"Wrote chunk {chunk_num} for language {lang} in voice {voice}.")


def write_samples(*, texts: dict[str, str], voices: list[str]) -> None:
    for lang, text in texts.items():
        for voice in voices:
            write_sample(lang=lang, text=text, voice=voice)


if __name__ == "__main__":
    voices = get_voices()
    # print_voices(voices, filter_fn=lambda voice: voice["Locale"] == "en-US")
    # print_voices(voices, filter_fn=lambda voice: "Multilingual" in voice["ShortName"])
    # print_voices(voices, filter_fn=lambda voice: voice["ShortName"] in VOICES)
    write_samples(texts=TEXTS, voices=VOICES)

"""Filtered voices (total=322, filtered=4):
1. {'Name': 'Microsoft Server Speech Text to Speech Voice (en-US, AndrewMultilingualNeural)', 'ShortName': 'en-US-AndrewMultilingualNeural', 'Gender': 'Male', 'Locale': 'en-US', 'LocaleName': 'English (United States)', 'SuggestedCodec': 'audio-24khz-48kbitrate-mono-mp3', 'FriendlyName': 'Microsoft AndrewMultilingual Online (Natural) - English (United States)', 'Status': 'GA', 'VoiceTag': {'ContentCategories': ['Conversation', 'Copilot'], 'VoicePersonalities': ['Warm', 'Confident', 'Authentic', 'Honest']}}
2. {'Name': 'Microsoft Server Speech Text to Speech Voice (en-US, AvaMultilingualNeural)', 'ShortName': 'en-US-AvaMultilingualNeural', 'Gender': 'Female', 'Locale': 'en-US', 'LocaleName': 'English (United States)', 'SuggestedCodec': 'audio-24khz-48kbitrate-mono-mp3', 'FriendlyName': 'Microsoft AvaMultilingual Online (Natural) - English (United States)', 'Status': 'GA', 'VoiceTag': {'ContentCategories': ['Conversation', 'Copilot'], 'VoicePersonalities': ['Expressive', 'Caring', 'Pleasant', 'Friendly']}}
3. {'Name': 'Microsoft Server Speech Text to Speech Voice (de-DE, SeraphinaMultilingualNeural)', 'ShortName': 'de-DE-SeraphinaMultilingualNeural', 'Gender': 'Female', 'Locale': 'de-DE', 'LocaleName': 'German (Germany)', 'SuggestedCodec': 'audio-24khz-48kbitrate-mono-mp3', 'FriendlyName': 'Microsoft SeraphinaMultilingual Online (Natural) - German (Germany)', 'Status':'GA', 'VoiceTag': {'ContentCategories': ['General'], 'VoicePersonalities': ['Friendly', 'Positive']}}
4. {'Name': 'Microsoft Server Speech Text to Speech Voice (de-DE, FlorianMultilingualNeural)', 'ShortName': 'de-DE-FlorianMultilingualNeural', 'Gender': 'Male', 'Locale': 'de-DE', 'LocaleName': 'German (Germany)', 'SuggestedCodec': 'audio-24khz-48kbitrate-mono-mp3', 'FriendlyName': 'Microsoft FlorianMultilingual Online (Natural) - German (Germany)', 'Status': 'GA', 'VoiceTag': {'ContentCategories': ['General'], 'VoicePersonalities': ['Friendly', 'Positive']}}
"""
