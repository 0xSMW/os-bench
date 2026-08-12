from __future__ import annotations
import copy
from pathlib import Path
from .contracts import contract_corpus_sha256
from .paths import repo_root
from .util import read_json,sha256_file,sha256_tree,write_json

def _measure(root:Path):
    out={"contract_corpus_sha256":contract_corpus_sha256(root)}
    paths={
      "evaluator_source_tree_sha256":root/'src/osbench',"test_source_tree_sha256":root/'tests',
      "reference_builder_source_tree_sha256":root/'reference/build',"raw_probe_source_tree_sha256":root/'probes',
      "workload_source_tree_sha256":root/'workloads',"payload_source_tree_sha256":root/'reference/guest',
    }
    for k,p in paths.items():out[k]=sha256_tree(p) if p.exists() else None
    for k,p in {"contract_schema_sha256":root/'contracts/schema/contract.schema.json',"benchmark_config_sha256":root/'config/benchmark.yaml',"qemu_config_sha256":root/'config/qemu.yaml'}.items():out[k]=sha256_file(p) if p.exists() else None
    return out

def synchronize_source_lock(*,check:bool=False)->dict:
    root=repo_root();path=root/'reference/lock.json';lock=read_json(path);measured=_measure(root);current=lock.setdefault('benchmark_artifacts',{});mismatches={k:{"expected":current.get(k),"observed":v} for k,v in measured.items() if current.get(k)!=v}
    if not check:
        current.update(measured);write_json(path,lock);mismatches={}
    return {"valid":not mismatches,"check":check,"mismatches":mismatches,"differences":mismatches,"measured":measured,"path":str(path)}
