"""Tracks session-wide token usage and timing."""
import time


class SessionStats:
    def __init__(self):
        self.start_time = time.time()
        self.total_tokens = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.turns = 0

    def record(self, usage: dict):
        self.turns += 1
        self.total_tokens += usage.get("total_tokens", 0) or 0
        self.total_prompt_tokens += usage.get("prompt_tokens", 0) or 0
        self.total_completion_tokens += usage.get("completion_tokens", 0) or 0

    def summary(self) -> str:
        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        return (
            f"{self.turns} turns · {self.total_tokens} tokens total "
            f"(prompt {self.total_prompt_tokens} / completion {self.total_completion_tokens}) "
            f"· session {mins}m{secs:02d}s"
        )
