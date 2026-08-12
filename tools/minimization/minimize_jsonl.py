#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,pathlib,subprocess,tempfile
ap=argparse.ArgumentParser();ap.add_argument('input',type=pathlib.Path);ap.add_argument('--predicate',required=True);ap.add_argument('--output',type=pathlib.Path,required=True);a=ap.parse_args()
rows=[json.loads(x) for x in a.input.read_text().splitlines() if x.strip()]
def fails(candidate):
 with tempfile.NamedTemporaryFile('w',delete=False) as f:
  for r in candidate:f.write(json.dumps(r,sort_keys=True)+'\n')
  name=f.name
 return subprocess.run(a.predicate.replace('{}',name),shell=True).returncode!=0
changed=True
while changed and len(rows)>1:
 changed=False
 for i in range(len(rows)):
  c=rows[:i]+rows[i+1:]
  if fails(c):rows=c;changed=True;break
a.output.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows));print(json.dumps({'remaining':len(rows),'output':str(a.output)}))
