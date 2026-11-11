"""Entry point for the codebase-audit engine. Works from any working directory:

    python <skill-dir>/scripts/run_engine.py --results-dir .codebase-audit/results ...

Relative paths (results, outputs, config) resolve against the current working
directory, i.e. the repository being audited.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
