"""
test_log_memory.py -- run the interaction scenes on (a) log memory
==================================================================

Run from the repo folder:
    python log_memory/test_log_memory.py

DRY_RUN = True  -> free retrieval check only
DRY_RUN = False -> also asks the LLM (15 calls). Needs ANTHROPIC_API_KEY in .env
Results go to log_memory/results/
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRY_RUN = True
SHOW_PROMPTS = False   # True = print the memory block for every turn


def load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load(HERE.parent / "runner.py")
LogMemory = load(HERE / "log_memory.py").LogMemory

if __name__ == "__main__":
    runner.run_tests("a_log", LogMemory, HERE / "results", DRY_RUN, SHOW_PROMPTS)
