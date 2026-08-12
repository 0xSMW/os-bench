#!/usr/bin/env python3
from pathlib import Path
import json,sys,yaml
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'src'))
from osbench.graph import contracts_for_workload
source=yaml.safe_load((root/'capability_graph/workloads.yaml').read_text()) or {}
rows={name:contracts_for_workload(name) for name in sorted(source)}
out=root/'capability_graph/workload_matrix.json';out.write_text(json.dumps({'schema_version':'osbench.workload_matrix.v1','workloads':rows},sort_keys=True,indent=2)+'\n')
md=['# Workload capability matrix','']
for name,contracts in rows.items():md.extend([f'## {name}','',', '.join(f'`{x}`' for x in contracts),''])
(root/'docs/CAPABILITY_COVERAGE.generated.md').write_text('\n'.join(md)+'\n');print(json.dumps({'workloads':len(rows),'output':str(out)},sort_keys=True))
