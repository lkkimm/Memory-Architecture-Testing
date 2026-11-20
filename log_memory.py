"""
BASELINE memory: log-style ("full log").

Every memory is appended to a list. Nothing is ever deleted, changed, or
filtered. When it's time to render, the WHOLE log (up to today) is handed to
the LLM, and the LLM has to figure out what matters.

It follows the interface from memory/README.md:
    write(...)     store what happened
    retrieve(...)  get the background for the next render

Later memory designs (RAG, temporal, ...) should keep these same two
functions, so the test script can swap them in without other changes.
"""


class LogMemory:

    def __init__(self):
        # the log is just a Python list of {"day": ..., "text": ...}
        self.log = []

    def write(self, day, text):
        """Store one memory at the end of the log."""
        memory = {"day": day, "text": text}
        self.log.append(memory)

    def retrieve(self, scene, now_day):
        """Return every memory up to now_day, oldest first, as one block of text.

        `scene` is unused here on purpose: the baseline doesn't pick
        memories based on the scene. (RAG will use it.)
        """
        lines = []
        for memory in self.log:
            if memory["day"] <= now_day:      # Jibo can't remember the future
                lines.append(f"Day {memory['day']}: {memory['text']}")
        return "\n".join(lines)


# Quick check:  python "memory/time-structures/log_memory.py"
if __name__ == "__main__":
    memory = LogMemory()
    memory.write(0, "Alex unboxed you.")
    memory.write(15, "Alex said she works at a bakery.")
    memory.write(140, "Alex started working at a hospital.")

    print("--- day 20 ---")
    print(memory.retrieve("greeting", 20))
    print("--- day 150 ---")
    print(memory.retrieve("greeting", 150))
