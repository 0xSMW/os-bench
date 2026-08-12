from __future__ import annotations
import os
from pathlib import Path

def repo_root() -> Path:
    override = os.environ.get("OSBENCH_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "pyproject.toml").exists() and (parent / "contracts").exists():
            return parent
    return Path.cwd().resolve()
