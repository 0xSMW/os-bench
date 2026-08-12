from __future__ import annotations
from typing import Any

def compare(reference:Any,candidate:Any,equivalence:dict[str,Any])->tuple[bool,Any|None]:
    kind=equivalence.get("type","exact")
    if kind in {"exact","semantic","relation","partial_order"}:
        ok=reference==candidate
    elif kind=="set": ok=set(map(str,reference))==set(map(str,candidate))
    elif kind=="multiset":
        from collections import Counter
        ok=Counter(map(str,reference))==Counter(map(str,candidate))
    elif kind=="range":
        tol=float(equivalence.get("tolerance",0));
        try: ok=abs(float(reference)-float(candidate))<=tol
        except Exception: ok=False
    else: ok=reference==candidate
    return ok,None if ok else {"kind":"observation_mismatch","reference":reference,"candidate":candidate,"equivalence":kind}
