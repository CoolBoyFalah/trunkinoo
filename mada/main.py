"""
MADA — My Advanced Digital Assistant
Run with:  python main.py
           python main.py --text      (text-only mode, no mic needed)
"""

import sys
import argparse
from config import USER_NAME, GROQ_API_KEY, ELEVENLABS_API_KEY

# ── startup checks ────────────────────────────────────────────────────────────

def _check_config():
    issues = []
    if not GROQ_API_KEY:
        issues.append("GROQ_API_KEY is missing in .env")
    if issues:
        print("\n[MADA] Configuration issues found:")
        for i in issues:
            print(f"  • {i}")
        print("\nCopy .env.example → .env and fill in your keys, then run again.\n")
        sys.exit(1)

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MADA — Personal AI Assistant")
    parser.add_argument("--text", action="store_true", help="Text-only mode (no microphone)")
    args = parser.parse_args()

    _check_config()

    from core.brain import MADABrain
    from voice.speaker import speak
    from scheduler import MADAScheduler

    brain = MADABrain()
    scheduler = MADAScheduler(brain, speak)
    scheduler.start()

    if args.text:
        _run_text_mode(brain, speak)
    else:
        _run_voice_mode(brain, speak)


def _run_voice_mode(brain, speak):
    from voice.listener import listen

    speak(
        f"Good day, {USER_NAME}. MADA is online and ready. "
        "Press Enter to speak, or type 'bye' to shut down."
    )

    while True:
        try:
            cmd = input("\n[Press ENTER to speak | type 'bye' to exit] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in ("bye", "exit", "quit", "shutdown"):
            speak(f"Understood, {USER_NAME}. Going offline. Goodbye.")
            break

        if cmd:
            # Typed input directly
            user_text = cmd
        else:
            # Voice input
            user_text = listen()

        if not user_text:
            speak("I didn't catch that. Could you try again?")
            continue

        response = brain.process(user_text)
        if response:
            speak(response)


def _run_text_mode(brain, speak):
    speak(f"MADA text mode active. How can I assist you, {USER_NAME}?")

    while True:
        try:
            user_input = input(f"\n[{USER_NAME}] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() in ("bye", "exit", "quit", "shutdown"):
            speak(f"Going offline. Goodbye, {USER_NAME}.")
            break

        response = brain.process(user_input)
        if response:
            speak(response)


if __name__ == "__main__":
    main()
