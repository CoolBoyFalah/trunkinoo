"""Autonomous background scheduler — runs tasks on a schedule even when you're away."""

import threading
import time
import schedule
from datetime import datetime

from config import BRIEFING_TIME, WRAPUP_TIME, USER_NAME


class MADAScheduler:
    def __init__(self, brain, speaker):
        self.brain = brain
        self.speaker = speaker
        self._thread = None
        self._running = False

    def start(self):
        schedule.every().day.at(BRIEFING_TIME).do(self._morning_briefing)
        schedule.every().day.at(WRAPUP_TIME).do(self._evening_wrapup)
        schedule.every(1).hours.do(self._check_urgent_emails)

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[MADA] Scheduler started. Morning briefing at {BRIEFING_TIME}, wrap-up at {WRAPUP_TIME}.")

    def stop(self):
        self._running = False
        schedule.clear()

    def _run_loop(self):
        while self._running:
            schedule.run_pending()
            time.sleep(30)

    def _morning_briefing(self):
        print("[MADA] Running morning briefing...")
        result = self.brain.quick_task(
            f"Good morning. Give {USER_NAME} a concise morning briefing: "
            "1) Check the last 10 unread emails and summarize the most important ones. "
            "2) List today's calendar events. "
            "3) Flag anything urgent or that needs a response. "
            "Keep it short and spoken-word friendly — no markdown."
        )
        self.speaker(result)

    def _evening_wrapup(self):
        print("[MADA] Running evening wrap-up...")
        result = self.brain.quick_task(
            f"Give {USER_NAME} a brief end-of-day summary: "
            "1) Any important emails that came in today that haven't been addressed. "
            "2) Tomorrow's first calendar events. "
            "3) Anything that needs attention tonight or tomorrow morning. "
            "Keep it concise and natural, no markdown."
        )
        self.speaker(result)

    def _check_urgent_emails(self):
        result = self.brain.quick_task(
            "Silently check for any emails marked urgent, or emails from VIP contacts. "
            "If there are none, respond with exactly: NO_URGENT. "
            "If there are urgent emails, give a one-sentence spoken alert."
        )
        if result and result.strip() != "NO_URGENT":
            print(f"[MADA] Urgent email alert: {result}")
            self.speaker(result)

    def run_task_now(self, task: str) -> str:
        """Run an arbitrary autonomous task immediately and return the result."""
        return self.brain.quick_task(task)
