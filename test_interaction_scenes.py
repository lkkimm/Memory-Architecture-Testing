"""
test_interaction_scenes.py -- run the multi-turn scenes on memory designs a, b, c
================================================================================

  (a) LogMemory            -- log_memory.py
  (b) RAGMemory            -- memory_architectures.py
  (c) TemporalGraphMemory  -- memory_architectures.py

For every scene, every architecture, and every turn it:
  1. fills the memory with the Mira timeline
  2. retrieves memories using THIS turn's query
  3. checks (for free) whether the memories the turn needs were retrieved
  4. (live mode only) asks the LLM for Jibo's reply + why, with the chat so far
  5. saves everything to results_interaction_scenes.csv

Run from the repo folder:
    python test_interaction_scenes.py

(b2) EmbeddingRAGMemory (embedding_rag.py) is added automatically if
sentence-transformers is installed; otherwise it is skipped.

DRY_RUN = True  -> only the retrieval check. No API calls, costs nothing.
DRY_RUN = False -> also calls the LLM: 15 turns x 3 architectures = 45 calls.
"""

import csv
import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = "claude-haiku-5-5"   # low-cost model (lab budget)
DRY_RUN = True
SHOW_PROMPTS = False         # True = print the memory block for every turn


def load(filename):
    """Import a file from this folder (works even if folder names have spaces)."""
    spec = importlib.util.spec_from_file_location(Path(filename).stem, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def env(key, default=None):
    """Read a value from the repo's .env file (searches this folder and up)."""
    folder = HERE
    while True:
        env_file = folder / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                name, _, value = line.partition("=")
                if name.strip() == key:
                    return value.strip()
        if folder.parent == folder:
            break
        folder = folder.parent
    if default is not None:
        return default
    raise KeyError(f"{key} is not set in .env")


scenes_file = load("interaction_scenes.py")
SCENES = scenes_file.INTERACTION_SCENES
CAREGIVER = scenes_file.CAREGIVER
TIMELINE = load("mira_timeline.py").TIMELINE
LogMemory = load("log_memory.py").LogMemory
architectures = load("memory_architectures.py")

ARCHITECTURES = {
    "a_log": LogMemory,
    "b_rag": architectures.RAGMemory,
    "c_temporal_graph": architectures.TemporalGraphMemory,
}

# (b2) embedding RAG -- only if sentence-transformers is installed AND the model loads
try:
    EmbeddingRAGMemory = load("embedding_rag.py").EmbeddingRAGMemory
    EmbeddingRAGMemory()   # try loading the model once
    ARCHITECTURES["b2_rag_embedding"] = EmbeddingRAGMemory
except Exception as error:
    print(f"(skipping b2_rag_embedding: {type(error).__name__})")

JIBO_PERSONA = (
    "You are Jibo, a friendly tabletop social robot who lives on Mira's kitchen counter. "
    "You have no arms. Say only what Jibo says out loud."
)

LENGTH_RULES = {
    "conversation": "Answer in one or two short sentences.",
    "bedtime": ("It's bedtime. If you're asked for a story, tell a short one (4-6 sentences). "
                "Otherwise answer in one or two short sentences."),
}

OUTPUT_FORMAT = (
    "Reply in exactly this format:\n"
    "SAY: <what Jibo says out loud>\n"
    "WHY: <which memories (by day number) you used for this reply, and why>"
)


# ---------------------------------------------------------------------------
# Building the memory
# ---------------------------------------------------------------------------
def build_memory(architecture_class):
    """Make an empty memory and write the whole timeline into it."""
    memory = architecture_class()
    for event in TIMELINE:
        # only the temporal graph uses the hand-written fact edges
        if architecture_class is architectures.TemporalGraphMemory:
            memory.write(event["day"], event["text"], event.get("edge"))
        else:
            memory.write(event["day"], event["text"])
    return memory


# ---------------------------------------------------------------------------
# Free retrieval check: were the needed memories in the prompt?
# ---------------------------------------------------------------------------
def retrieved_days(memory_block):
    """All day numbers that appear as 'Day N:' in the retrieved text."""
    days = []
    for number in re.findall(r"Day (\d+):", memory_block):
        days.append(int(number))
    return days


def check_retrieval(turn, memory_block):
    """For each needed memory: 'found', 'MISSING', or 'check by hand'.

    It reads the day from the text, e.g. 'day 145 paper crane' -> day 145,
    'day 15-130 bakery' -> any day from 15 to 130 counts.
    """
    found_days = retrieved_days(memory_block)
    results = []
    for need in turn["memories_needed"]:
        match = re.search(r"day (\d+)(?:-(\d+))?", need)
        if match is None:
            results.append((need, "check by hand"))
            continue

        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start

        hit = False
        for day in found_days:
            if start <= day <= end:
                hit = True
        results.append((need, "found" if hit else "MISSING"))
    return results


# ---------------------------------------------------------------------------
# LLM call (live mode only)
# ---------------------------------------------------------------------------
def build_system_prompt(scene, memory_block):
    return (
        f"{JIBO_PERSONA}\n"
        f"{LENGTH_RULES[scene['interaction_type']]}\n\n"
        f"Scene: {scene['situation']}\n\n"
        f"Today is day {scene['now_day']} (day 0 is the day you arrived). "
        f"Your memories:\n{memory_block}\n\n"
        f"{OUTPUT_FORMAT}"
    )


def split_reply(text):
    """Split 'SAY: ... WHY: ...' into two strings."""
    say, why = text, ""
    if "WHY:" in text:
        say, why = text.split("WHY:", 1)
    say = say.replace("SAY:", "").strip()
    return say, why.strip()


def ask_llm(client, system_prompt, chat_so_far):
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=system_prompt,
        messages=chat_so_far,
    )
    return split_reply(response.content[0].text)


def run_all_checks():
    """Retrieval check for every scene x architecture x turn. Returns a summary dict."""
    summary = {}
    for arch_name, arch_class in ARCHITECTURES.items():
        summary[arch_name] = [0, 0]
        for scene in SCENES:
            memory = build_memory(arch_class)
            for turn in scene["turns"]:
                block = memory.retrieve(turn["query"], scene["now_day"])
                for need, result in check_retrieval(turn, block):
                    if result == "found":
                        summary[arch_name][0] += 1
                        summary[arch_name][1] += 1
                    elif result == "MISSING":
                        summary[arch_name][1] += 1
    return summary


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    client = None
    if not DRY_RUN:
        import anthropic
        # If the lab's Parley setup needs a different client line, copy it from
        # the repo's other scripts and replace these two lines.
        base_url = env("ANTHROPIC_BASE_URL", default="")
        client = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"), base_url=base_url or None)

    rows = []
    summary = {}   # architecture -> [found, total]
    for name in ARCHITECTURES:
        summary[name] = [0, 0]

    for scene in SCENES:
        print("=" * 78)
        print(f"{scene['id']}  (day {scene['now_day']}, {scene['interaction_type']})")
        print("=" * 78)

        for arch_name, arch_class in ARCHITECTURES.items():
            memory = build_memory(arch_class)
            chat_so_far = []   # the conversation in THIS scene (not long-term memory)
            print(f"\n  --- {arch_name} ---")

            turn_number = 1
            for turn in scene["turns"]:
                memory_block = memory.retrieve(turn["query"], scene["now_day"])
                checks = check_retrieval(turn, memory_block)

                found = 0
                checkable = 0
                missing = []
                for need, result in checks:
                    if result == "found":
                        found += 1
                        checkable += 1
                    elif result == "MISSING":
                        checkable += 1
                        missing.append(need)
                summary[arch_name][0] += found
                summary[arch_name][1] += checkable

                status = f"{found}/{checkable} needed memories retrieved"
                if missing:
                    status += "   MISSING: " + "; ".join(missing)
                print(f"  turn {turn_number}: {status}")

                if SHOW_PROMPTS:
                    print("    " + memory_block.replace("\n", "\n    "))

                say, why = "", ""
                if not DRY_RUN:
                    chat_so_far.append({"role": "user", "content": f"{CAREGIVER}: {turn['line']}"})
                    system_prompt = build_system_prompt(scene, memory_block)
                    say, why = ask_llm(client, system_prompt, chat_so_far)
                    chat_so_far.append({"role": "assistant", "content": say})
                    print(f"    {CAREGIVER}: {turn['line']}")
                    print(f"    Jibo: {say}")
                    print(f"    why:  {why}")

                rows.append({
                    "scene": scene["id"], "architecture": arch_name, "turn": turn_number,
                    "line": turn["line"], "retrieved": f"{found}/{checkable}",
                    "missing": "; ".join(missing), "jibo_says": say, "why": why,
                    "good_response": turn["good_response"],
                    "memory_block": memory_block,
                })
                turn_number += 1

    print("\n" + "=" * 78)
    print("RETRIEVAL SUMMARY (needed memories that made it into the prompt)")
    for arch_name in summary:
        found, total = summary[arch_name]
        print(f"  {arch_name:<18} {found}/{total}")

    suffix = "retrieval_check" if DRY_RUN else "llm_run"
    out_path = HERE / "results" / f"{suffix}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} rows to {out_path}")
