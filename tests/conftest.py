# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | Recall Wk1 Day 1 — pytest config + path setup | prev: NEW
import sys
from pathlib import Path

# src/ layout — make the package importable in tests without installing.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
