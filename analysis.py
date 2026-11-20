"""
analysis.py -- extra FREE experiments (no LLM calls)
====================================================

Experiment 1: how much does the retrieval size matter?
    Sweep RAG's TOP_K and the temporal graph's RECENT_N (3, 6, 10)
    and re-run the retrieval check.

Experiment 2: where do the needed memories sit in the log prompt?
    For the log baseline everything is retrieved, so if it fails, it's the LLM.
    One known LLM weakness is "lost in the middle": models pay more attention
    to the start and end of a long context. This lists where each needed
    memory sits (as % of the way through the log) so the LLM run can test it.

Experiment 3: how big is each prompt?
    Average size of the memory block per architecture (cost / context length).

Run:  python analysis.py
Writes results/analysis.md
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(filename):
    spec = importlib.util.spec_from_file_location(Path(filename).stem, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load("test_interaction_scenes.py")
SCENES = runner.SCENES
ARCHITECTURES = runner.ARCHITECTURES
architectures = runner.architectures

report = []   # lines of markdown


def add(line=""):
    print(line)
    report.append(line)


# ---------------------------------------------------------------------------
# Experiment 1: retrieval size sweep
# ---------------------------------------------------------------------------
add("## Experiment 1: retrieval size sweep")
add("")
add("Needed memories that made it into the prompt (all 3 scenes, 15 turns).")
add("")
add("| Setting | 3 | 6 (default) | 10 |")
add("|---|---|---|---|")

sizes = [3, 6, 10]

row = "| b_rag TOP_K |"
for k in sizes:
    architectures.RAGMemory.TOP_K = k
    found, total = runner.run_all_checks()["b_rag"]
    row += f" {found}/{total} |"
add(row)
architectures.RAGMemory.TOP_K = 6

row = "| c_temporal_graph RECENT_N |"
for n in sizes:
    architectures.TemporalGraphMemory.RECENT_N = n
    found, total = runner.run_all_checks()["c_temporal_graph"]
    row += f" {found}/{total} |"
add(row)
architectures.TemporalGraphMemory.RECENT_N = 6

if "b2_rag_embedding" in ARCHITECTURES:
    row = "| b2_rag_embedding TOP_K |"
    for k in sizes:
        ARCHITECTURES["b2_rag_embedding"].TOP_K = k
        found, total = runner.run_all_checks()["b2_rag_embedding"]
        row += f" {found}/{total} |"
    add(row)
    ARCHITECTURES["b2_rag_embedding"].TOP_K = 6
add("")


# ---------------------------------------------------------------------------
# Experiment 2: position of needed memories in the log
# ---------------------------------------------------------------------------
add("## Experiment 2: where needed memories sit in the log prompt (a_log)")
add("")
add("0% = first line of the memory block, 100% = last line.")
add("")
add("| Scene | Turn | Needed memory | Position | Zone |")
add("|---|---|---|---|---|")

zone_counts = {"start": 0, "middle": 0, "end": 0}
for scene in SCENES:
    memory = runner.build_memory(ARCHITECTURES["a_log"])
    block = memory.retrieve("", scene["now_day"])
    days_in_order = runner.retrieved_days(block)
    total_lines = len(days_in_order)

    turn_number = 1
    for turn in scene["turns"]:
        for need in turn["memories_needed"]:
            match = runner.re.search(r"day (\d+)", need)
            if match is None or "-" in need.split(match.group(0))[1][:1]:
                continue   # skip ranges like 'day 15-130' and unchecked needs
            day = int(match.group(1))
            if day not in days_in_order:
                continue
            index = days_in_order.index(day)
            percent = round(100 * index / (total_lines - 1))
            if percent < 25:
                zone = "start"
            elif percent > 75:
                zone = "end"
            else:
                zone = "middle"
            zone_counts[zone] += 1
            add(f"| {scene['id']} | {turn_number} | {need} | {percent}% | {zone} |")
        turn_number += 1
add("")
add(f"Totals: start {zone_counts['start']}, middle {zone_counts['middle']}, end {zone_counts['end']}")
add("")


# ---------------------------------------------------------------------------
# Experiment 3: prompt size
# ---------------------------------------------------------------------------
add("## Experiment 3: memory block size per architecture")
add("")
add("| Architecture | Avg characters | ~Tokens (chars / 4) |")
add("|---|---|---|")
for arch_name, arch_class in ARCHITECTURES.items():
    sizes_seen = []
    for scene in SCENES:
        memory = runner.build_memory(arch_class)
        for turn in scene["turns"]:
            block = memory.retrieve(turn["query"], scene["now_day"])
            sizes_seen.append(len(block))
    average = round(sum(sizes_seen) / len(sizes_seen))
    add(f"| {arch_name} | {average} | {average // 4} |")
add("")

out_path = HERE / "results" / "analysis.md"
out_path.write_text("# Free analyses (no LLM calls)\n\n" + "\n".join(report) + "\n")
print(f"\nSaved {out_path}")
