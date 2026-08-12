#!/usr/bin/env python3
from __future__ import annotations
import collections,json,pathlib,yaml
ROOT=pathlib.Path(__file__).resolve().parents[2]
contracts=[]
for p in (ROOT/'contracts').rglob('*.yaml'):
 if 'schema' not in p.parts:contracts.append(yaml.safe_load(p.read_text()))
by_level=collections.Counter(c['level'] for c in contracts);by_domain=collections.Counter(c['domain'] for c in contracts);by_transport=collections.Counter(c['transport'] for c in contracts)
doc={'schema_version':'osbench.coverage.v1','contracts':len(contracts),'by_level':dict(sorted(by_level.items())),'by_domain':dict(sorted(by_domain.items())),'by_transport':dict(sorted(by_transport.items())),'workloads':len(list((ROOT/'workloads/manifests').glob('*.yaml')))}
(ROOT/'artifacts/coverage').mkdir(parents=True,exist_ok=True);(ROOT/'artifacts/coverage/report.json').write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n');print(json.dumps(doc,sort_keys=True))
