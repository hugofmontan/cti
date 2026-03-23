"""Pacote de projeções e DCF."""

import sys
from pathlib import Path

_PB = Path(__file__).resolve().parent
if str(_PB) not in sys.path:
    sys.path.insert(0, str(_PB))
