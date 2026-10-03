"""Make the vendored parser packages importable on their own, as they will be once on PyPI."""

import sys
from pathlib import Path

COMPONENTS = Path(__file__).parent.parent / "custom_components"
for integration in ("ela", "eddystone", "minew"):
    sys.path.insert(0, str(COMPONENTS / integration))
