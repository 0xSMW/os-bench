from __future__ import annotations
import random, string
from typing import Any
from .util import sha256_value

FAMILY_DIFFICULTY={
 "primitive":"basic","boundary":"intermediate","state_transition":"intermediate",
 "composition":"advanced","concurrency":"advanced","isolation":"advanced",
 "failure":"advanced","persistence":"advanced","exhaustion":"advanced",
 "workload":"macro","performance":"macro",
}

def generic_case(contract: dict[str,Any], *, seed:int, family:str, index:int, profile:str) -> dict[str,Any]:
    rng=random.Random(seed)
    token=''.join(rng.choice(string.ascii_lowercase+string.digits) for _ in range(12))
    scale=[0,1,2,4,16,64,256,4096][rng.randrange(8)]
    fault=rng.choice(contract.get("fault_injection") or ["none"])
    timeout=float(contract.get("timeouts",{}).get("case_seconds",10))
    case={
      "schema_version":"osbench.case.v1","benchmark_version":"0.1.0",
      "contract":contract["id"],"domain":contract["domain"],"level":contract["level"],
      "family":family,"case_family":family,"difficulty":FAMILY_DIFFICULTY[family],
      "seed":seed,"index":index,"profile":profile,"prerequisites":contract.get("prerequisites",[]),
      "setup":{"clean_snapshot": index%4!=0,"temporary_root":f"/tmp/osbench-{token}"},
      "stimulus":{"operation":contract["operation"],"token":token,"scale":scale,"fault":fault,"arguments":[rng.randrange(-4,17),rng.randrange(0,8193)]},
      "expected":{"comparison":contract.get("equivalence",{}).get("type","semantic"),"observables":contract.get("observables",[])},
      "resource_limits":{"memory_mb":max(16,min(512,scale or 16)),"processes":max(4,min(128,(scale or 4))),"files":max(8,min(1024,(scale or 8)*2))},
      "timeout_seconds":timeout,"cleanup":contract.get("cleanup_invariants",[]),
      "generator":{"implementation":contract["generator"]["implementation"],"version":contract["generator"].get("version","1"),"probe":contract["generator"].get("probe")},
      "transport":contract.get("transport","host"),"provenance":contract.get("sources",[]),
    }
    case["case_id"]=f"{contract['id']}:{sha256_value(case)[:16]}"
    return case
