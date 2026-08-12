from __future__ import annotations
import os
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('OSBENCH_ROOT',str(ROOT))
os.environ.setdefault('OSBENCH_REFERENCE_MODE','local')

@pytest.fixture(scope='session')
def root()->Path:return ROOT
