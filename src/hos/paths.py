"""Canonical project paths. Every stage resolves files through these."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"


def ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
