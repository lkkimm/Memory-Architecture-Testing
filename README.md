# Memory Architecture Testing

Testing how different memory architectures hold up when a social robot (Jibo) has
**longer, multi-turn interactions** with its caregiver, instead of one-line greetings.

Part of the Jibo Memory UROP (MIT Media Lab, Personal Robots Group).
Research log by Leyun Kim.

---

## Research question

> Greeting scenes are too short to tell memory designs apart: a one-line "Welcome home!"
> looks the same whether memory works or not. **If we give Jibo richer interactions
> (bedtime wind-downs, 4–5 turn conversations), where and why does each memory
> architecture fail?**

Sub-questions (from the 11/13 meeting):
1. Which memories does each architecture actually put in front of the LLM?
2. When the right memory *is* there, does the LLM use it? (needs the LLM run)
3. Does the LLM pay more attention to the start or the end of the context?

---

## Setup

```
mira_timeline.py ──► memory architecture ──► retrieved memories ──► LLM prompt ──► Jibo's reply
  (33 memories)       write() / retrieve()     ("Day N: ...")        + chat so far    SAY + WHY
```

### Memory architectures

| | Architecture | File | Idea |
|---|---|---|---|
| a | Log-style (baseline) | `log_memory.py` | Put the whole history in the prompt. Let the LLM sort it out. |
| b | RAG (TF-IDF) | `memory_architectures.py` | Return the 6 memories most similar to the query (word overlap). No sense of time. |
| b2 | RAG (embeddings) | `embedding_rag.py` | Same as b, but matches meaning (`all-MiniLM-L6-v2`). *Not run yet, see limitations.* |
| c | Temporal graph | `memory_architectures.py` | Zep / Graphiti idea: facts as (subject, relation, object) with valid-from / valid-until. New facts end old ones. Plus the 6 most recent events. |

All architectures share the same interface: `write(day, text)` and `retrieve(query, now_day)`.

### Scenes (`interaction_scenes.py`)

| Scene | Day | Type | Stresses |
|---|---|---|---|
| `bedtime_hospital_week` | 147 | bedtime, 5 turns | picking meaningful memories out of filler; old + new together |
| `conversation_back_from_seoul` | 121 | conversation, 5 turns | a long gap; another person (Sam); a turn with **no** memory behind it |
| `conversation_work_talk` | 150 | conversation, 5 turns | a contradiction (bakery → hospital) landing in a specific turn |

Each turn lists the memories it needs, a good response, and expected failure modes,
so failures can be pinned to an exact turn.

### Method

- **Free retrieval check:** for every scene × architecture × turn, check whether the memories the turn needs ended up in the prompt. No LLM calls.
- **Free analyses** (`analysis.py`): retrieval-size sweep, position of needed memories in the log, prompt size.
- **LLM run** (`DRY_RUN = False`): Jibo replies turn by turn with the chat so far, in the format `SAY: … / WHY: <memories used, by day>`. 15 turns × 3 architectures = 45 calls on Haiku.

---

## Results (11/20)

### 1. Retrieval check: needed memories that reached the prompt

| Scene | a · Log | b · RAG | c · Temporal graph |
|---|---|---|---|
| Bedtime | 9/9 | 6/9 | 8/9 |
| Back from Seoul | 5/5 | 3/5 | 5/5 |
| Work talk | 4/4 | 3/4 | 4/4 |
| **Total** | **18/18** | **12/18** | **17/18** |

Full per-turn table: [`results/retrieval_check.csv`](results/retrieval_check.csv)

### 2. Retrieval size sweep

| Setting | 3 | 6 (default) | 10 |
|---|---|---|---|
| RAG `TOP_K` | 10/18 | 12/18 | 12/18 |
| Temporal graph `RECENT_N` | 15/18 | 17/18 | 18/18 |

### 3. Prompt size (memory block only)

| Architecture | ~Tokens |
|---|---|
| a · Log | ~440 |
| b · RAG | ~100 |
| c · Temporal graph | ~195 |

Position analysis: [`results/analysis.md`](results/analysis.md)

---

## Findings

**RAG fails on the first turn of every scene, and more retrieval doesn't fix it.**
Openers like "Did you miss me?", "Tell me a bedtime story" and "Ugh, what a day" share
almost no words with any memory. With nothing to match, RAG falls back to the oldest
memories (unboxing, naming, day 0–18). Raising `TOP_K` from 6 to 10 adds nothing (12/18 → 12/18),
so the problem is the **query**, not the retrieval size.

**RAG hits the contradiction before the LLM is even called.** For "Ugh, what a day"
(query: "long day work tired"), RAG retrieves the *bakery* memories, because they contain
"tired" and "work". The hospital memory never reaches the prompt, so Jibo has no way to get it right.

**The temporal graph keeps a stale fact.** On day 121 it lists "Mira is visiting her parents
in Seoul" as *true now*: nothing ever told the graph she came back. It knows when facts
start; it doesn't know when they quietly end.

**The temporal graph only keeps facts and recent events, so meaningful old episodes fall through.**
"She felt stuck at the bakery and wanted to help people" (day 130) isn't a fact and isn't
recent, so it's missing exactly when Mira asks "Did I make the right call leaving the bakery?".
`RECENT_N = 10` fixes it here, but that's tuning to this dataset, not a real fix.

**The log retrieves everything, so any failure of the log has to come from the LLM.**
That's what the LLM run tests.

## Limitations (what I'd tell my PI)

- **The dataset is biased toward recent memories.** 12 of 17 needed memories sit in the last
  25% of the log, 4 in the middle, 1 at the start. That's not a fair "lost in the middle" test yet.
- **The log is short** (~440 tokens). A real year with Jibo would be thousands of memories,
  which is where the log baseline should start to strain.
- **The retrieval check reads day numbers**, so it can tell a memory was *present*, not whether it was *used*.
- **The embedding RAG (b2) hasn't run yet**: the model download is blocked in the environment I used. It runs fine locally.
- **The temporal graph edges are hand-written.** Real Graphiti extracts them with an LLM, which adds its own errors.
- **No LLM run yet**: it needs the lab API key.

## Next steps

1. Run the LLM pass (45 calls) and sort each failure: *memory missing* / *retrieved but ignored* / *misweighted*.
2. Run b2 (embedding RAG) and see whether meaning-matching fixes the vague-opener failure.
3. Build a position test: move one key memory to the start / middle / end of a padded log.
4. Scale the timeline (hundreds of filler memories) to stress the log baseline.
5. Architecture d: weighted memories with decay, threshold dropping, and similar memories adding weight.

---

## How to run

```bash
pip install -r requirements.txt

python test_interaction_scenes.py   # retrieval check (free) -> results/retrieval_check.csv
python analysis.py                  # free analyses          -> results/analysis.md
```

For the LLM run: put `ANTHROPIC_API_KEY=...` in a `.env` file in this folder
(never commit it; it's in `.gitignore`), then set `DRY_RUN = False` in
`test_interaction_scenes.py`. Results go to `results/llm_run.csv`.

## Files

| File | What it is |
|---|---|
| `interaction_scenes.py` | the 3 multi-turn scenes |
| `mira_timeline.py` | the memory dataset (33 memories, incl. filler) |
| `log_memory.py` | (a) log baseline |
| `memory_architectures.py` | (b) RAG and (c) temporal graph |
| `embedding_rag.py` | (b2) RAG with embeddings |
| `test_interaction_scenes.py` | runs scenes × architectures × turns |
| `analysis.py` | free extra experiments |
| `results/` | outputs |
