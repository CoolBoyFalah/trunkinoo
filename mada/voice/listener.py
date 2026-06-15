"""Voice input: records from microphone and transcribes with OpenAI Whisper."""

import numpy as np
import sounddevice as sd
import whisper

from config import VOICE_RECORD_SECONDS

_model = None


def _load_model():
    global _model
    if _model is None:
        print("[MADA] Loading Whisper model (first time only, ~1 min)...")
        _model = whisper.load_model("base")
        print("[MADA] Whisper ready.")
    return _model


def listen(prompt: str = "Listening") -> str:
    """
    Record audio until silence is detected (up to VOICE_RECORD_SECONDS),
    then transcribe and return the text.
    """
    model = _load_model()
    sample_rate = 16000
    chunk_size = 1024
    silence_threshold = 0.008
    silence_required = int(1.8 * sample_rate / chunk_size)   # ~1.8s of silence to stop
    max_chunks = int(VOICE_RECORD_SECONDS * sample_rate / chunk_size)

    print(f"[MADA] {prompt}... (speak now)")

    chunks = []
    silence_count = 0
    started = False

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            chunks.append(chunk.copy())
            energy = float(np.sqrt(np.mean(chunk ** 2)))

            if energy > silence_threshold:
                started = True
                silence_count = 0
            elif started:
                silence_count += 1
                if silence_count >= silence_required:
                    break

    if not chunks or not started:
        return ""

    audio = np.concatenate(chunks).flatten()
    print("[MADA] Transcribing...")
    result = model.transcribe(audio, language="en", fp16=False)
    text = result["text"].strip()
    if text:
        print(f"[You] {text}")
    return text
