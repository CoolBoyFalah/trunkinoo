"""Voice output: converts text to speech using ElevenLabs, with pyttsx3 fallback."""

import io
import threading

from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

_lock = threading.Lock()


def speak(text: str) -> None:
    """Speak text aloud. Uses ElevenLabs if configured, else pyttsx3 fallback."""
    if not text or not text.strip():
        return

    print(f"[MADA] {text}")

    with _lock:
        if ELEVENLABS_API_KEY:
            _speak_elevenlabs(text)
        else:
            _speak_pyttsx3(text)


def _speak_elevenlabs(text: str) -> None:
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        play(audio)
    except Exception as e:
        print(f"[MADA] ElevenLabs error ({e}), falling back to system voice.")
        _speak_pyttsx3(text)


def _speak_pyttsx3(text: str) -> None:
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[MADA] pyttsx3 error: {e}")
