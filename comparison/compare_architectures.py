"""
compare_architectures.py -- all architectures side by side (FREE, no LLM calls)
==============================================================================

Run from the repo folder:
    python comparison/compare_architectures.py

  Table 1: retrieval check per scene, for every architecture
  Table 2: how much does the retrieval size matter? (sweep 3 / 6 / 10)
  Table 3: where do the needed memories sit in the log prompt?
           ("lost in the middle": LLMs tend to attend more to the start and end)
  Table 4: how big is each architecture's memory block?

Writes comparison/results.md
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load(ROOT / "runner.py")
LogMemory = load(ROOT / "log_memory" / "log_memory.py").LogMemory
RAGMemory = load(ROOT / "rag_memory" / "rag_memory.py").RAGMemory
TemporalGraphMemory = load(ROOT / "temporal_graph" / "temporal_graph.py").TemporalGraphMemory

ARCHITECTURES = {
    "a_log": LogMemory,
    "b_rag_tfidf": RAGMemory,
    "c_temporal_graph": TemporalGraphMemory,
}

try:
    EmbeddingRAGMemory = load(ROOT / "rag_memory" / "embedding_rag.py").EmbeddingRAGMemory
    EmbeddingRAGMemory()   # check the model loads
    ARCHITECTURES["b2_rag_embedding"] = EmbeddingRAGMemory
except Exception as error:
    print(f"(skipping b2_rag_embedding: {type(error).__name__})")

report = []   # lines of markdown


def add(line=""):
    print(line)
    report.append(line)


def scene_score(architecture_class, scene):
    """(found, total) needed memories for one scene."""
    memory = runner.build_memory(architecture_class)
    found = 0
    total = 0
    for turn in scene["turns"]:
        block = memory.retrieve(turn["query"], scene["now_day"])
        for need, result in runner.check_retrieval(turn, block):
            if result == "found":
                found += 1
                total += 1
            elif result == "MISSING":
                total += 1
    return found, total


# ---------------------------------------------------------------------------
# Table 1: retrieval check per scene
# ---------------------------------------------------------------------------
add("## 1. Needed memories that reached the prompt")
add("")
header = "| Scene |"
divider = "|---|"
for name in ARCHITECTURES:
    header += f" {name} |"
    divider += "---|"
add(header)
add(divider)

totals = {}
for name in ARCHITECTURES:
    totals[name] = [0, 0]

for scene in runner.SCENES:
    row = f"| {scene['id']} |"
    for name, arch_class in ARCHITECTURES.items():
        found, total = scene_score(arch_class, scene)
        totals[name][0] += found
        totals[name][1] += total
        row += f" {found}/{total} |"
    add(row)

row = "| **Total** |"
for name in ARCHITECTURES:
    row += f" **{totals[name][0]}/{totals[name][1]}** |"
add(row)
add("")


# ---------------------------------------------------------------------------
# Table 2: retrieval size sweep
# ---------------------------------------------------------------------------
add("## 2. Retrieval size sweep")
add("")
add("| Setting | 3 | 6 (default) | 10 |")
add("|---|---|---|---|")

sizes = [3, 6, 10]

row = "| RAG (TF-IDF) TOP_K |"
for k in sizes:
    RAGMemory.TOP_K = k
    found, total = runner.count_retrieval(RAGMemory)
    row += f" {found}/{total} |"
add(row)
RAGMemory.TOP_K = 6

if "b2_rag_embedding" in ARCHITECTURES:
    row = "| RAG (embedding) TOP_K |"
    for k in sizes:
        EmbeddingRAGMemory.TOP_K = k
        found, total = runner.count_retrieval(EmbeddingRAGMemory)
        row += f" {found}/{total} |"
    add(row)
    EmbeddingRAGMemory.TOP_K = 6

row = "| Temporal graph RECENT_N |"
for n in sizes:
    TemporalGraphMemory.RECENT_N = n
    found, total = runner.count_retrieval(TemporalGraphMemory)
    row += f" {found}/{total} |"
add(row)
TemporalGraphMemory.RECENT_N = 6
add("")


# ---------------------------------------------------------------------------
# Table 3: position of needed memories in the log
# ---------------------------------------------------------------------------
add("## 3. Where needed memories sit in the log prompt (a_log)")
add("")
add("0% = first line of the memory block, 100% = last line.")
add("")
add("| Scene | Turn | Needed memory | Position | Zone |")
add("|---|---|---|---|---|")

zone_counts = {"start": 0, "middle": 0, "end": 0}
for scene in runner.SCENES:
    memory = runner.build_memory(LogMemory)
    block = memory.retrieve("", scene["now_day"])
    days_in_order = runner.retrieved_days(block)
    total_lines = len(days_in_order)

    turn_number = 1
    for turn in scene["turns"]:
        for need in turn["memories_needed"]:
            match = runner.re.search(r"day (\d+)(-\d+)?", need)
            if match is None or match.group(2):
                continue   # skip ranges like 'day 15-130'
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
# Table 4: prompt size
# ---------------------------------------------------------------------------
add("## 4. Memory block size per architecture")
add("")
add("| Architecture | Avg characters | ~Tokens (chars / 4) |")
add("|---|---|---|")
for name, arch_class in ARCHITECTURES.items():
    sizes_seen = []
    for scene in runner.SCENES:
        memory = runner.build_memory(arch_class)
        for turn in scene["turns"]:
            block = memory.retrieve(turn["query"], scene["now_day"])
            sizes_seen.append(len(block))
    average = round(sum(sizes_seen) / len(sizes_seen))
    add(f"| {name} | {average} | {average // 4} |")
add("")

out_path = HERE / "results.md"
out_path.write_text("# Comparison of memory architectures (free checks, no LLM calls)\n\n"
                    + "\n".join(report) + "\n")
print(f"\nSaved {out_path.relative_to(ROOT)}")
