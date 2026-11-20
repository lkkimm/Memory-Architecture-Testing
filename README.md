# Memory Architecture Testing

Testing how different memory architectures hold up when a social robot (Jibo) has
**longer, multi-turn interactions** with its caregiver, instead of one-line greetings.

Part of the Jibo Memory UROP (MIT Media Lab, Personal Robots Group). By Leyun Kim.

**Full analysis: [WRITEUP.md](WRITEUP.md)**

---

## Results so far

Needed memories that reached the LLM prompt (free retrieval check, no LLM calls):

| Scene | a · Log | b · RAG | c · Temporal graph |
|---|---|---|---|
| Bedtime | 9/9 | 6/9 | 8/9 |
| Back from Seoul | 5/5 | 3/5 | 5/5 |
| Work talk | 4/4 | 3/4 | 4/4 |
| **Total** | **18/18** | **12/18** | **17/18** |

- **RAG** fails on every scene's vague opening line, and retrieves bakery memories for "Ugh, what a day" (the contradiction fails before the LLM is called).
- **Temporal graph** keeps a stale fact ("Mira is in Seoul" on the day she's back) and drops meaningful old episodes.
- **Log** retrieves everything, so its failures can only come from the LLM. That's the next run.

---

## Repo layout

```
Memory-Architecture-Testing/
├── scenes.py                 ALL scenes: 12 greeting + 3 interaction (bedtime, conversations)
├── mira_timeline.py          the shared memory dataset (33 memories, day 0-149)
├── runner.py                 shared test loop + helpers (every test script uses it)
│
├── log_memory/               (a) log baseline: whole history in the prompt
│   ├── log_memory.py
│   ├── test_log_memory.py
│   └── results/
│
├── rag_memory/               (b) RAG: most similar memories to the query
│   ├── rag_memory.py             TF-IDF version (word overlap)
│   ├── embedding_rag.py          embedding version (meaning)
│   ├── test_rag_memory.py        tests both
│   └── results/
│
├── temporal_graph/           (c) temporal graph: facts with valid-from / valid-until
│   ├── temporal_graph.py
│   ├── test_temporal_graph.py
│   └── results/
│
├── comparison/               all architectures side by side
│   ├── compare_architectures.py
│   └── results.md
│
├── WRITEUP.md                full analysis
└── requirements.txt
```

**How it fits together:** each test script loads its architecture and calls
`runner.run_tests()`. The runner fills the memory with `mira_timeline.py`, plays
every interaction scene from `scenes.py` turn by turn, checks whether each turn's
needed memories were retrieved, and saves a CSV to that architecture's `results/`.

Every architecture has the same two functions, so the runner can swap them freely:

```python
memory.write(day, text)            # store what happened
memory.retrieve(query, now_day)    # get the memories for the next LLM call
```

---

## How to run

```bash
pip install -r requirements.txt
```

Run from the repo folder:

| What | Command | Output |
|---|---|---|
| Test the log | `python log_memory/test_log_memory.py` | `log_memory/results/` |
| Test RAG (TF-IDF + embedding) | `python rag_memory/test_rag_memory.py` | `rag_memory/results/` |
| Test the temporal graph | `python temporal_graph/test_temporal_graph.py` | `temporal_graph/results/` |
| Compare all of them | `python comparison/compare_architectures.py` | `comparison/results.md` |
| Check the scenes | `python scenes.py` | prints a summary |

By default every test is a **free retrieval check** (`DRY_RUN = True`, no API calls).

**LLM run:** put `ANTHROPIC_API_KEY=...` in a `.env` file in the repo folder (it's in
`.gitignore`, so it won't be committed), then set `DRY_RUN = False` in the test
script you want. Each architecture costs 15 calls on Haiku. Jibo answers each turn
as `SAY: ...` plus `WHY: <memories used, by day>`, saved to `results/<name>_llm_run.csv`.
If the lab's API setup needs a different client, change `make_client()` in `runner.py`.

**Embedding RAG:** needs `sentence-transformers`. The model (~90 MB) downloads the
first time; if it can't, the RAG test skips it and runs TF-IDF only.

---

## Adding a new architecture

1. Make a folder, e.g. `weighted_memory/`, with a class that has `write()` and `retrieve()`.
   Every line `retrieve()` returns should start with `Day N:`.
2. Copy one of the test scripts into it and change the class it loads.
3. Add it to `ARCHITECTURES` in `comparison/compare_architectures.py`.
