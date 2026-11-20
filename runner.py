"""
runner.py -- shared helpers for every test script
================================================

Each architecture folder has its own small test script (for example
log_memory/test_log_memory.py). All of them call run_tests() from here, so the
test logic lives in ONE place.

run_tests(name, ArchitectureClass, results_folder) does, for every interaction
scene and every turn:
  1. fills the memory with the Mira timeline
  2. retrieves memories using THIS turn's query
  3. checks (for free) whether the memories the turn needs were retrieved
  4. (live mode only) asks the LLM for Jibo's reply + why, with the chat so far
  5. saves everything to a CSV in that architecture's results/ folder

dry_run=True  -> only the retrieval check. No API calls, costs nothing.
dry_run=False -> also calls the LLM: 15 calls per architecture.
"""

import csv
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = "claude-haiku-5-5"   # low-cost model (lab budget)


def load(path):
    """Import a Python file by its path (works even if folder names have spaces)."""
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def env(key, default=None):
    """Read a value from a .env file (searches the repo folder and up)."""
    folder = ROOT
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


scenes_file = load("scenes.py")
SCENES = scenes_file.INTERACTION_SCENES
CAREGIVER = scenes_file.CAREGIVER
TIMELINE = load("mira_timeline.py").TIMELINE

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
    uses_edges = getattr(architecture_class, "USES_EDGES", False)
    for event in TIMELINE:
        if uses_edges:
            # only the temporal graph uses the hand-written fact edges
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


def count_retrieval(architecture_class):
    """Quiet version for the comparison script: returns (found, total) over all scenes."""
    found = 0
    total = 0
    for scene in SCENES:
        memory = build_memory(architecture_class)
        for turn in scene["turns"]:
            block = memory.retrieve(turn["query"], scene["now_day"])
            for need, result in check_retrieval(turn, block):
                if result == "found":
                    found += 1
                    total += 1
                elif result == "MISSING":
                    total += 1
    return found, total


# ---------------------------------------------------------------------------
# LLM call (live mode only)
# ---------------------------------------------------------------------------
def make_client():
    import anthropic
    # If the lab's Parley setup needs a different client line, change it here.
    base_url = env("ANTHROPIC_BASE_URL", default="")
    return anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY"), base_url=base_url or None)


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


# ---------------------------------------------------------------------------
# The test loop every architecture uses
# ---------------------------------------------------------------------------
def run_tests(name, architecture_class, results_folder, dry_run=True, show_prompts=False):
    """Run all interaction scenes on one architecture. Returns (found, total)."""
    client = None if dry_run else make_client()

    rows = []
    found_all = 0
    total_all = 0

    for scene in SCENES:
        print("=" * 78)
        print(f"{name}: {scene['id']}  (day {scene['now_day']}, {scene['interaction_type']})")
        print("=" * 78)

        memory = build_memory(architecture_class)
        chat_so_far = []   # the conversation in THIS scene (not long-term memory)

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
            found_all += found
            total_all += checkable

            status = f"{found}/{checkable} needed memories retrieved"
            if missing:
                status += "   MISSING: " + "; ".join(missing)
            print(f"  turn {turn_number}: {status}")

            if show_prompts:
                print("    " + memory_block.replace("\n", "\n    "))

            say, why = "", ""
            if not dry_run:
                chat_so_far.append({"role": "user", "content": f"{CAREGIVER}: {turn['line']}"})
                system_prompt = build_system_prompt(scene, memory_block)
                say, why = ask_llm(client, system_prompt, chat_so_far)
                chat_so_far.append({"role": "assistant", "content": say})
                print(f"    {CAREGIVER}: {turn['line']}")
                print(f"    Jibo: {say}")
                print(f"    why:  {why}")

            rows.append({
                "scene": scene["id"], "architecture": name, "turn": turn_number,
                "line": turn["line"], "retrieved": f"{found}/{checkable}",
                "missing": "; ".join(missing), "jibo_says": say, "why": why,
                "good_response": turn["good_response"],
                "memory_block": memory_block,
            })
            turn_number += 1

    print(f"\n{name}: {found_all}/{total_all} needed memories retrieved")

    results_folder = Path(results_folder)
    results_folder.mkdir(parents=True, exist_ok=True)
    suffix = "retrieval_check" if dry_run else "llm_run"
    out_path = results_folder / f"{name}_{suffix}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {out_path.relative_to(ROOT)}")
    return found_all, total_all
