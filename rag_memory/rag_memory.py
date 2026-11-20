"""
rag_memory.py -- architecture (b): RAG with TF-IDF vectors
=========================================================

Interface (same as every architecture):
    write(day, text)          store what happened
    retrieve(query, now_day)  get the memories for the next LLM call

Every line that retrieve() returns starts with "Day N:". The test scripts use
that to check which memories were retrieved.

See embedding_rag.py in this folder for (b2), the same idea with an
embedding model that matches meaning instead of shared words.
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
