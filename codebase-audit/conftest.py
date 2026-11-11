import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
# Plugin root (for `tools`) and the orchestrator skill's scripts dir (for `engine`).
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "skills" / "codebase-audit" / "scripts"))
