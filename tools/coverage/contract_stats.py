#!/usr/bin/env python3
from __future__ import annotations
import json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'))
from osbench.contracts import validate_contracts
report=validate_contracts(); print(json.dumps({'valid':report.valid,**report.stats()},sort_keys=True,indent=2))
raise SystemExit(0 if report.valid else 1)
