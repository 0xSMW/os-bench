#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,pathlib
from osbench.tracing import trace_workload

def main()->int:
 p=argparse.ArgumentParser();p.add_argument('names',nargs='*');p.add_argument('--profile');a=p.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2]
 names=a.names or sorted(path.stem for path in (root/'workloads/manifests').glob('*.yaml'))
 results=[]
 for name in names:
  try:results.append(trace_workload(name,profile=a.profile))
  except Exception as exc:results.append({'workload':name,'error':f'{type(exc).__name__}: {exc}'})
 print(json.dumps({'results':results},sort_keys=True,indent=2));return 1 if any('error' in x for x in results) else 0
if __name__=='__main__':raise SystemExit(main())
