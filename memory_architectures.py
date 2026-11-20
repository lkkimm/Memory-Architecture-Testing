"""
memory_architectures.py -- architectures (b) and (c) from the meeting notes
==========================================================================

  (a) Log-style memory  -> already in log_memory.py (LogMemory)
  (b) RAG               -> RAGMemory, below
  (c) Temporal graph    -> TemporalGraphMemory, below (the Zep / Graphiti idea)

All of them keep the same two functions as LogMemory, so the test script can
swap them without other changes:
    write(day, text)          store what happened
    retrieve(query, now_day)  get the memories for the next LLM call

Every line that retrieve() returns starts with "Day N:". The test script uses
that to check which memories were retrieved.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ===========================================================================
# (b) RAG -- retrieve only the memories that look most similar to the query
# ===========================================================================
class RAGMemory:
    """
    Standard RAG: turn every memory and the query into vectors, then return
    the TOP_K memories whose vectors are closest to the query.

    The vectors here are TF-IDF (word-overlap based, free and offline).
    Real systems usually use embedding models, which also match synonyms
    ("tired" ~ "exhausted"). To try that later, only the two vector lines in
    retrieve() need to change -- everything else stays the same.

    Note: RAG has NO idea of time. It never prefers new memories over old ones.
    """

    TOP_K = 6   # how many memories go into the prompt

    def __init__(self):
        self.memories = []

    def write(self, day, text):
        self.memories.append({"day": day, "text": text})

    def retrieve(self, query, now_day):
        # 1. only memories up to today (Jibo can't remember the future)
        past = []
        for memory in self.memories:
            if memory["day"] <= now_day:
                past.append(memory)

        texts = []
        for memory in past:
            texts.append(memory["text"])

        # 2. turn the memories and the query into vectors
        vectorizer = TfidfVectorizer(stop_words="english")
        memory_vectors = vectorizer.fit_transform(texts)
        query_vector = vectorizer.transform([query])

        # 3. similarity between the query and every memory (0 = nothing in common)
        scores = cosine_similarity(query_vector, memory_vectors)[0]

        scored = []
        for i in range(len(past)):
            scored.append((scores[i], past[i]))

        # 4. keep the TOP_K most similar ones
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:self.TOP_K]

        # 5. show them oldest first, so they read like a story
        top.sort(key=lambda pair: pair[1]["day"])
        lines = []
        for score, memory in top:
            lines.append(f"Day {memory['day']}: {memory['text']}")
        return "\n".join(lines)


# ===========================================================================
# (c) Temporal graph -- facts with a "valid from / valid until" time
# ===========================================================================
class TemporalGraphMemory:
    """
    The Zep / Graphiti idea, kept small.

    Two things are stored:
      - episodes : everything that happened (like the log)
      - edges    : facts as (subject, relation, object), each with
                   valid_from (the day it became true) and
                   valid_to   (the day it stopped being true, or None)

    When a new fact has the same subject + relation as an old one, the old one
    is NOT deleted. It gets a valid_to date instead. So Jibo still knows
    "Mira USED TO work at a bakery" -- it just isn't true anymore.

    retrieve() returns:
      1. facts that are true now
      2. facts that used to be true (with when they ended)
      3. the most recent episodes
      4. how long ago the last memory was

    Simplification vs. real Graphiti: Graphiti searches the graph with the
    query; here the graph is small, so all facts are returned. And the edges
    are written by hand in the timeline instead of extracted by an LLM.
    """

    RECENT_N = 6   # how many recent episodes go into the prompt

    def __init__(self):
        self.episodes = []
        self.edges = []

    def write(self, day, text, edge=None):
        self.episodes.append({"day": day, "text": text})

        if edge is None:
            return

        subject, relation, obj = edge

        # an older fact with the same subject + relation stops being true today
        for old in self.edges:
            same_fact = old["subject"] == subject and old["relation"] == relation
            if same_fact and old["valid_to"] is None:
                old["valid_to"] = day

        self.edges.append({
            "subject": subject, "relation": relation, "object": obj,
            "valid_from": day, "valid_to": None,
        })

    def retrieve(self, query, now_day):
        # `query` is unused: all facts are returned (see the note above)
        true_now = []
        used_to_be_true = []

        for edge in self.edges:
            if edge["valid_from"] > now_day:
                continue   # Jibo doesn't know this fact yet

            fact = f"{edge['subject']} {edge['relation']} {edge['object']}"

            # it ended only if it ended on or before today
            ended = edge["valid_to"] is not None and edge["valid_to"] <= now_day
            if ended:
                used_to_be_true.append(
                    f"Day {edge['valid_from']}: {fact} (NO LONGER TRUE since day {edge['valid_to']})")
            else:
                true_now.append(f"Day {edge['valid_from']}: {fact}")

        # most recent episodes up to today
        past_episodes = []
        for episode in self.episodes:
            if episode["day"] <= now_day:
                past_episodes.append(episode)
        recent = past_episodes[-self.RECENT_N:]

        recent_lines = []
        for episode in recent:
            recent_lines.append(f"Day {episode['day']}: {episode['text']}")

        # how long since the last memory
        if past_episodes:
            last_day = past_episodes[-1]["day"]
            gap_line = f"Your last memory is from day {last_day} ({now_day - last_day} days ago)."
        else:
            gap_line = "You have no memories yet."

        parts = [
            "Facts that are true now:",
            "\n".join(true_now) if true_now else "(none)",
            "",
            "Facts that USED to be true:",
            "\n".join(used_to_be_true) if used_to_be_true else "(none)",
            "",
            "Most recent things that happened:",
            "\n".join(recent_lines) if recent_lines else "(none)",
            "",
            gap_line,
        ]
        return "\n".join(parts)
