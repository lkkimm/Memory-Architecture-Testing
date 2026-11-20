"""
embedding_rag.py -- architecture (b2): RAG with a real embedding model
=====================================================================

Same as RAGMemory in memory_architectures.py, but the vectors come from an
embedding model instead of TF-IDF. Embeddings match MEANING, not just shared
words, so "I'm back!" can match "visiting Seoul for two weeks".

Needs:  pip install sentence-transformers
The model (~90 MB) downloads the first time. It runs locally, so it costs no
API budget.
"""

from sentence_transformers import SentenceTransformer


class EmbeddingRAGMemory:
    TOP_K = 6
    MODEL_NAME = "all-MiniLM-L6-v2"   # small and fast

    def __init__(self):
        self.model = SentenceTransformer(self.MODEL_NAME)
        self.memories = []

    def write(self, day, text):
        # write time: embed ONCE and save the vector next to the text
        vector = self.model.encode(text, normalize_embeddings=True)
        self.memories.append({"day": day, "text": text, "vector": vector})

    def retrieve(self, query, now_day):
        # retrieve time: embed the query the SAME way
        query_vector = self.model.encode(query, normalize_embeddings=True)

        scored = []
        for memory in self.memories:
            if memory["day"] <= now_day:
                # vectors are normalized, so the dot product = cosine similarity
                score = float(memory["vector"] @ query_vector)
                scored.append((score, memory))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:self.TOP_K]

        top.sort(key=lambda pair: pair[1]["day"])
        lines = []
        for score, memory in top:
            lines.append(f"Day {memory['day']}: {memory['text']}")
        return "\n".join(lines)
