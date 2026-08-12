from __future__ import annotations
from typing import Any,Callable

def minimize_sequence(items:list[Any],fails:Callable[[list[Any]],bool])->list[Any]:
    result=list(items);granularity=2
    while len(result)>=2:
        chunk=max(1,len(result)//granularity);reduced=False
        for start in range(0,len(result),chunk):
            candidate=result[:start]+result[start+chunk:]
            if candidate and fails(candidate):result=candidate;granularity=max(2,granularity-1);reduced=True;break
        if not reduced:
            if granularity>=len(result):break
            granularity=min(len(result),granularity*2)
    return result
