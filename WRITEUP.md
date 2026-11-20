# Memory Architecture Testing: Write-up

Jibo Memory UROP, MIT Media Lab Personal Robots Group. Leyun Kim, November 20, 2026.
Repo: github.com/lkkimm/Memory-Architecture-Testing

## 1. Motivation

Greeting scenes are too short to tell memory designs apart. A greeting is one line, so a good design and a weak one can both produce "Welcome home!" and look the same. To see where memory actually helps or breaks, Jibo needs interactions with more room to use what he remembers.

**Research question:** if Jibo has richer interactions (a bedtime wind-down and 4 to 5 turn conversations), where and why does each memory architecture fail?

Sub-questions:

- Which memories does each architecture actually put in front of the LLM?
- When the right memory is in the prompt, does the LLM use it?
- Does the LLM pay more attention to the start or the end of its context?

## 2. Setup

### Dataset

One hand-written timeline between Jibo and his caregiver Mira (`mira_timeline.py`), 33 memories from day 0 (Jibo arrives) to day 149. It includes deliberate stress points: a fact that changes (bakery job, then hospital job on day 140), a two-week gap (Seoul trip, days 107 to 120), another person (her brother Sam), and ordinary filler memories (weather, TV, chores) so that retrieval has wrong things to grab.

### Scenes

Three multi-turn scenes, five turns each, on the same timeline (`INTERACTION_SCENES` in `scenes.py`). Every turn lists the memories it needs, what a good response does, and how a weak design fails, so a failure can be pinned to one turn.

| Scene | Day | Type | What it stresses |
| --- | --- | --- | --- |
| Bedtime after her first hospital week | 147 | bedtime | choosing meaningful memories over filler; old and new memories together |
| Back from Seoul | 121 | conversation | a long gap; another person; a turn with no memory behind it |
| Work talk | 150 | conversation | a contradiction (bakery vs. hospital) landing in a specific turn |

The 12 original greeting scenes are also in `scenes.py` (`GREETING_SCENES`), but they aren't tested yet: several need memories from later in the year that the timeline doesn't have.

### Architectures

| | Architecture | Folder | Idea |
| --- | --- | --- | --- |
| a | Log (baseline) | `log_memory/` | Put the whole history in the prompt and let the LLM sort it out. |
| b | RAG (TF-IDF) | `rag_memory/` | Return the 6 memories most similar in wording to the turn's query. No sense of time. |
| b2 | RAG (embeddings) | `rag_memory/` | Same as b but matches meaning. Written, not run yet. |
| c | Temporal graph | `temporal_graph/` | Zep / Graphiti idea. Facts carry valid-from and valid-until days, so a new fact ends an old one without deleting it. Plus the 6 most recent events. |

All share one interface: `write(day, text)` and `retrieve(query, now_day)`.

### Method

A free retrieval check: for each scene, architecture and turn, test whether the needed memories reached the prompt. No LLM calls. Plus three free analyses: a retrieval-size sweep, where needed memories sit in the log, and prompt size. The live LLM run (15 calls per architecture on Haiku, replies as SAY plus WHY) is ready but not run yet.

## 3. Results

### Needed memories that reached the prompt

| Scene | a. Log | b. RAG | c. Temporal graph |
| --- | --- | --- | --- |
| Bedtime | 9/9 | 6/9 | 8/9 |
| Back from Seoul | 5/5 | 3/5 | 5/5 |
| Work talk | 4/4 | 3/4 | 4/4 |
| **Total** | **18/18** | **12/18** | **17/18** |

### Retrieval size sweep

| Setting | 3 | 6 (default) | 10 |
| --- | --- | --- | --- |
| RAG top-k | 10/18 | 12/18 | 12/18 |
| Temporal graph recent events | 15/18 | 17/18 | 18/18 |

### Prompt size (memory block only)

| Architecture | Approx. tokens |
| --- | --- |
| a. Log | 440 |
| b. RAG | 100 |
| c. Temporal graph | 195 |

### Position of needed memories in the log

Of 17 needed memories, 12 sit in the last quarter of the log, 4 in the middle, and 1 at the start.

Full tables: `comparison/results.md`. Per-turn results: each architecture's `results/` folder.

## 4. Findings

**RAG fails on the opening turn of every scene, and more retrieval doesn't help.** Openers like "Did you miss me?", "Tell me a bedtime story" and "Ugh, what a day" share almost no words with any memory. With nothing to match, RAG falls back to the oldest memories. Raising top-k from 6 to 10 changes nothing, so the problem is the query, not the size of the retrieval.

**RAG walks into the contradiction before the LLM is called.** For "Ugh, what a day", RAG retrieves bakery memories because they contain "tired" and "work". The hospital memory never reaches the prompt, so Jibo cannot get it right.

**The temporal graph keeps a stale fact.** On day 121 it still lists "Mira is visiting her parents in Seoul" as true, because nothing told it she came back. It knows when facts start, not when they quietly end.

**The temporal graph drops meaningful old episodes.** "She felt stuck at the bakery and wanted to help people" (day 130) is neither a stored fact nor recent, so it is missing exactly when Mira asks whether leaving the bakery was the right call. Keeping 10 recent events fixes it here, but that is tuning to this dataset.

**The log retrieves everything, so any log failure has to come from the LLM.** That is what the live run will test.

## 5. Limitations

- The dataset leans recent: most needed memories sit near the end, so it is not yet a fair test of start-versus-end attention.
- The log is short (about 440 tokens). A real year would be thousands of memories, which is where the baseline should strain.
- The retrieval check shows a memory was present, not that it was used.
- The embedding RAG has not run yet.
- The temporal graph's facts are hand-written; real Graphiti extracts them with an LLM, which adds its own errors.
- No LLM run yet.

## 6. Next steps

1. Run the live LLM pass and sort each failure: memory missing, retrieved but ignored, or misweighted.
2. Run the embedding RAG and see whether matching meaning fixes the vague-opener failure.
3. Position test: move one key memory to the start, middle and end of a padded log.
4. Scale the timeline to hundreds of memories to stress the log baseline, and extend it so the greeting scenes can be tested too.
5. Architecture d: weighted memories with decay, dropping below a threshold, and similar memories adding weight.
6. Future work: associative memory, where one triggered memory pulls in related ones.
