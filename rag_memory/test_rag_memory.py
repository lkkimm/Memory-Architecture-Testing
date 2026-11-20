"""
test_rag_memory.py -- run the interaction scenes on (b) RAG memory
=================================================================

Tests both versions:
  b_rag_tfidf      rag_memory.py     (word overlap, always runs)
  b2_rag_embedding embedding_rag.py  (meaning, needs: pip install sentence-transformers)

Run from the repo folder:
    python rag_memory/test_rag_memory.py

DRY_RUN = True  -> free retrieval check only
DRY_RUN = False -> also asks the LLM (15 calls per version). Needs ANTHROPIC_API_KEY in .env
Results go to rag_memory/results/
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRY_RUN = True
SHOW_PROMPTS = False


def load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load(HERE.parent / "runner.py")
RAGMemory = load(HERE / "rag_memory.py").RAGMemory

if __name__ == "__main__":
    runner.run_tests("b_rag_tfidf", RAGMemory, HERE / "results", DRY_RUN, SHOW_PROMPTS)

    # (b2) only if sentence-transformers is installed AND the model can download
    try:
        EmbeddingRAGMemory = load(HERE / "embedding_rag.py").EmbeddingRAGMemory
        EmbeddingRAGMemory()   # loads the model once to check it works
    except Exception as error:
        print(f"\n(skipping b2_rag_embedding: {type(error).__name__}: {error})")
    else:
        runner.run_tests("b2_rag_embedding", EmbeddingRAGMemory, HERE / "results", DRY_RUN, SHOW_PROMPTS)
