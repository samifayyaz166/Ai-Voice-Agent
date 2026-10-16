import io
import re

from groq import Groq

HALLUCINATIONS = {
    "thank you",
    "thanks",
    "thanks for watching",
    "thank you for watching",
    "thank you so much",
    "you",
    "bye",
    "bye bye",
    "okay",
    "the end",
    "subscribe",
}

MIN_AUDIO_BYTES = 16000
NO_SPEECH_LIMIT = 0.6


def _normalize(text):
    return re.sub(r"[^a-z ]", "", text.lower()).strip()


def transcribe_audio(audio_bytes, api_key, language="en"):

    if not audio_bytes or len(audio_bytes) < MIN_AUDIO_BYTES:
        return ""

    client = Groq(api_key=api_key)

    result = client.audio.transcriptions.create(
        file=("recording.wav", io.BytesIO(audio_bytes)),
        model="whisper-large-v3",
        response_format="verbose_json",
        temperature=0.0,
        language=language,
    )

    text = (getattr(result, "text", "") or "").strip()

    if not text:
        return ""

    segments = getattr(result, "segments", None) or []

    if segments:
        probs = []
        for s in segments:
            if isinstance(s, dict):
                probs.append(s.get("no_speech_prob", 0))
            else:
                probs.append(getattr(s, "no_speech_prob", 0))

        if sum(probs) / len(probs) > NO_SPEECH_LIMIT:
            return ""

    if _normalize(text) in HALLUCINATIONS:
        return ""

    return text