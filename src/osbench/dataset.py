from __future__ import annotations
import collections, hashlib, random, tempfile
from pathlib import Path
from typing import Any
from .constants import BENCHMARK_VERSION, CASE_FAMILIES
from .contracts import contract_corpus_sha256, load_contracts, validate_contracts
from .generators import generic_case
from .paths import repo_root
from .util import jsonl_load, jsonl_write, sha256_file, sha256_value, write_json

PUBLIC_FAMILY_COUNTS={
 "primitive":446,"boundary":401,"state_transition":323,"composition":402,
 "concurrency":187,"isolation":36,"failure":357,"persistence":78,
 "exhaustion":265,"workload":92,"performance":73,
}

def _family_schedule(total:int, profile:str, seed:int) -> list[str]:
    if profile=="public" and total==sum(PUBLIC_FAMILY_COUNTS.values()):
        families=[f for f,n in PUBLIC_FAMILY_COUNTS.items() for _ in range(n)]
    else:
        families=[CASE_FAMILIES[i%len(CASE_FAMILIES)] for i in range(total)]
    random.Random(seed^0x05B3E11).shuffle(families)
    return families

def generate_cases(*, profile:str="public", seed:int=1, cases_per_contract:int=10, contracts:list[dict[str,Any]]|None=None) -> list[dict[str,Any]]:
    items=sorted(contracts or load_contracts(),key=lambda c:c["id"])
    schedule=_family_schedule(len(items)*cases_per_contract,profile,seed)
    cases=[]; cursor=0
    for ci,c in enumerate(items):
        for index in range(cases_per_contract):
            family=schedule[cursor]; cursor+=1
            case_seed=int.from_bytes(hashlib.sha256(f"{seed}:{c['id']}:{index}:{profile}".encode()).digest()[:8],"big")
            cases.append(generic_case(c,seed=case_seed,family=family,index=index,profile=profile))
    return cases

def dataset_paths(profile:str="public") -> tuple[Path,Path]:
    root=repo_root(); version="v0.1"
    return root/"dataset"/profile/version/"cases.jsonl", root/"dataset"/"manifests"/f"{version}-{profile}.json"

def build_dataset(*,profile:str="public",seed:int=1,cases_per_contract:int=10) -> dict[str,Any]:
    report=validate_contracts()
    if not report.valid: raise ValueError("invalid Contract corpus")
    cases=generate_cases(profile=profile,seed=seed,cases_per_contract=cases_per_contract,contracts=report.contracts)
    case_path,manifest_path=dataset_paths(profile)
    jsonl_write(case_path,cases)
    family_counts=dict(collections.Counter(c["family"] for c in cases))
    manifest={
      "schema_version":"osbench.dataset_manifest.v1","benchmark_version":BENCHMARK_VERSION,
      "profile":profile,"seed":seed,"cases_per_contract":cases_per_contract,
      "contract_count":len(report.contracts),"case_count":len(cases),
      "contract_corpus_sha256":contract_corpus_sha256(),"cases_sha256":sha256_file(case_path),
      "dataset_sha256":sha256_value(cases),"family_counts":dict(sorted(family_counts.items())),
      "path":str(case_path.relative_to(repo_root())),
    }
    write_json(manifest_path,manifest); return manifest

def check_determinism(*,profile:str="public",seed:int=1,cases_per_contract:int=10)->bool:
    a=generate_cases(profile=profile,seed=seed,cases_per_contract=cases_per_contract)
    b=generate_cases(profile=profile,seed=seed,cases_per_contract=cases_per_contract)
    return a==b

def validate_dataset(path:Path|None=None)->dict[str,Any]:
    case_path,manifest_path=dataset_paths("public")
    path=path or case_path
    if not path.exists(): return {"valid":False,"issues":[f"missing {path}"]}
    rows=jsonl_load(path); issues=[]; ids=set()
    known={c["id"] for c in load_contracts()}
    required={"case_id","contract","domain","level","family","seed","setup","stimulus","expected","timeout_seconds"}
    for i,row in enumerate(rows,1):
        miss=required-set(row)
        if miss: issues.append(f"line {i}: missing {sorted(miss)}")
        if row.get("contract") not in known: issues.append(f"line {i}: unknown Contract")
        if row.get("case_id") in ids: issues.append(f"line {i}: duplicate case id")
        ids.add(row.get("case_id"))
    if manifest_path.exists() and path==case_path:
        import json
        m=json.loads(manifest_path.read_text())
        if m.get("case_count")!=len(rows): issues.append("manifest case_count mismatch")
        if m.get("cases_sha256")!=sha256_file(path): issues.append("manifest cases_sha256 mismatch")
    return {"valid":not issues,"case_count":len(rows),"issues":issues}
