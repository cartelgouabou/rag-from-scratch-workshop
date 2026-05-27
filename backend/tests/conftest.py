import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_ROOT = BACKEND_ROOT.parent / "notebooks"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(NOTEBOOKS_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOKS_ROOT))
