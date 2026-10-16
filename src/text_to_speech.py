import asyncio
import io
import re

import edge_tts

DEFAULT_VOICE = "en-US-JennyNeural"


def clean_text_for_speech(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~]{1,3}", "", text)
    text = re.sub(r"\s*\n\s*", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


async def _edge_speech(text, voice):
    communicate = edge_tts.Communicate(text=text, voice=voice)

    chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])

    return b"".join(chunks)


def _gtts_speech(text):
    from gtts import gTTS

    buffer = io.BytesIO()
    gTTS(text=text, lang="en").write_to_fp(buffer)
    return buffer.getvalue()


def generate_speech(text, voice=DEFAULT_VOICE):

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    spoken_text = clean_text_for_speech(text)

    if not spoken_text:
        raise ValueError("Nothing to speak.")

    # 1) Edge TTS (2 koshish)
    for attempt in range(2):
        try:
            audio = asyncio.run(_edge_speech(spoken_text, voice))
            if audio:
                print("[TTS] Edge TTS OK")
                return audio
        except Exception as error:
            print(f"[TTS] Edge TTS attempt {attempt + 1} failed: {error!r}")

    # 2) Backup: gTTS
    try:
        audio = _gtts_speech(spoken_text)
        if audio:
            print("[TTS] gTTS backup OK")
            return audio
    except Exception as error:
        print(f"[TTS] gTTS failed: {error!r}")

    raise RuntimeError("Could not generate voice. Check your internet.")