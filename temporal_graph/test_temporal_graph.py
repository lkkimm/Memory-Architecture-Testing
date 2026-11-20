"""
test_temporal_graph.py -- run the interaction scenes on (c) the temporal graph
=============================================================================

Run from the repo folder:
    python temporal_graph/test_temporal_graph.py

DRY_RUN = True  -> free retrieval check only
DRY_RUN = False -> also asks the LLM (15 calls). Needs ANTHROPIC_API_KEY in .env
Results go to temporal_graph/results/
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
TemporalGraphMemory = load(HERE / "temporal_graph.py").TemporalGraphMemory

if __name__ == "__main__":
    runner.run_tests("c_temporal_graph", TemporalGraphMemory, HERE / "results", DRY_RUN, SHOW_PROMPTS)
