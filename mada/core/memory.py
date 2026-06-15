import json
from datetime import datetime
from pathlib import Path
from config import MEMORY_FILE, HISTORY_FILE


class MADAMemory:
    """Persistent long-term memory and conversation history for MADA."""

    def __init__(self):
        self._mem: dict = self._load(MEMORY_FILE)
        self._history: list = self._load(HISTORY_FILE)

    # ── persistence ───────────────────────────────────────────────────────────

    def _load(self, path: Path):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {} if "memory" in path.name else []

    def _save_mem(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self._mem, f, indent=2, ensure_ascii=False)

    def _save_history(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self._history[-60:], f, indent=2, ensure_ascii=False)

    # ── long-term key/value memory ────────────────────────────────────────────

    def save(self, key: str, value: str) -> str:
        self._mem[key] = {"value": value, "saved_at": datetime.now().isoformat()}
        self._save_mem()
        return f"Remembered: {key} = {value}"

    def recall(self, key: str) -> str:
        if key == "all":
            if not self._mem:
                return "No memories stored yet."
            lines = [f"- {k}: {v['value']}" for k, v in self._mem.items()]
            return "\n".join(lines)
        entry = self._mem.get(key)
        if entry:
            return f"{key}: {entry['value']} (saved {entry['saved_at'][:10]})"
        return f"No memory found for '{key}'."

    def get_all_as_context(self) -> str:
        if not self._mem:
            return ""
        lines = [f"  - {k}: {v['value']}" for k, v in self._mem.items()]
        return "What you remember about your user:\n" + "\n".join(lines)

    def delete(self, key: str) -> str:
        if key in self._mem:
            del self._mem[key]
            self._save_mem()
            return f"Forgotten: {key}"
        return f"No memory found for '{key}'."

    # ── conversation history ───────────────────────────────────────────────────

    def add_message(self, role: str, content):
        self._history.append({"role": role, "content": content})
        self._save_history()

    def get_history(self) -> list:
        return list(self._history[-20:])

    def clear_history(self):
        self._history = []
        self._save_history()
