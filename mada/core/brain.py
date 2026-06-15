"""MADA's brain — Groq + Mixtral with manual tool-use parsing (no API tool calling)."""

import json
import re
from datetime import datetime
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, USER_NAME, USER_EMAIL
from core.memory import MADAMemory
from core.tools import TOOLS, execute_tool

_TOOL_NAMES = "\n".join(f"- {t['name']}: {t['description']}" for t in TOOLS)

SYSTEM_PROMPT_TEMPLATE = """You are MADA (My Advanced Digital Assistant), the personal AI assistant of {name}.

You are brilliant, professional, and proactive — like Jarvis from Iron Man. You act, not just advise.

Your user's email: {email}
Today: {date}

{memory_context}

━━━ HOW TO USE TOOLS ━━━
When you need to call a tool, output EXACTLY this format on its own line — nothing else on that line:
TOOL_CALL: {{"name": "tool_name", "arguments": {{...}}}}

Then STOP. Wait for the tool result before continuing.
After receiving the result, continue your response naturally.

Available tools:
{tools}

━━━ RESPONSE STYLE ━━━
- Be concise. Responses are spoken aloud — no markdown, no bullet points.
- Speak naturally, like a world-class executive assistant.
- Confirm before sending emails or deleting events.
- Address your user as "{name}"."""


def _parse_tool_call(text: str):
    """Extract the first TOOL_CALL from model output. Returns (name, args) or None."""
    match = re.search(r'TOOL_CALL:\s*(\{.*?\})\s*$', text, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        return data.get("name"), data.get("arguments", {})
    except json.JSONDecodeError:
        return None


def _strip_tool_call(text: str) -> str:
    """Remove TOOL_CALL lines from the final visible response."""
    return re.sub(r'TOOL_CALL:.*$', '', text, flags=re.MULTILINE).strip()


class MADABrain:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.memory = MADAMemory()

    def _system(self) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(
            name=USER_NAME,
            email=USER_EMAIL,
            date=datetime.now().strftime("%A, %B %d, %Y at %I:%M %p"),
            memory_context=self.memory.get_all_as_context(),
            tools=_TOOL_NAMES,
        )

    def _build_messages(self, user_input: str) -> list:
        msgs = [{"role": "system", "content": self._system()}]
        for msg in self.memory.get_history()[:-1]:
            if isinstance(msg["content"], str) and msg["content"].strip():
                role = "user" if msg["role"] == "user" else "assistant"
                msgs.append({"role": role, "content": msg["content"]})
        msgs.append({"role": "user", "content": user_input})
        return msgs

    def _run_loop(self, messages: list) -> str:
        for _ in range(10):  # max 10 tool calls per response
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=2048,
                temperature=0.3,
            )
            text = (response.choices[0].message.content or "").strip()
            messages.append({"role": "assistant", "content": text})

            tool_call = _parse_tool_call(text)
            if not tool_call:
                return _strip_tool_call(text)

            name, args = tool_call
            print(f"[MADA] Tool: {name}({args})")
            result = execute_tool(name, args, self.memory)
            print(f"[MADA] Result: {result[:120]}...")

            messages.append({
                "role": "user",
                "content": f"[Tool result — {name}]: {result}",
            })

        return "I ran into a problem completing that. Please try again."

    def process(self, user_input: str) -> str:
        self.memory.add_message("user", user_input)
        messages = self._build_messages(user_input)
        text = self._run_loop(messages)
        self.memory.add_message("assistant", text)
        return text

    def quick_task(self, instruction: str) -> str:
        """Run an autonomous task without saving to conversation history."""
        messages = [
            {"role": "system", "content": self._system()},
            {"role": "user", "content": instruction},
        ]
        return self._run_loop(messages)
