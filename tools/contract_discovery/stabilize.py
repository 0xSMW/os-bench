#!/usr/bin/env python3
from __future__ import annotations
import argparse,collections,json,pathlib

def main()->int:
 p=argparse.ArgumentParser(description='Summarize repeated oracle observations before accepting a Contract')
 p.add_argument('observations',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path);a=p.parse_args()
 rows=[json.loads(x) for x in a.observations.read_text().splitlines() if x.strip()]
 signatures=collections.Counter(json.dumps(row.get('normalized',row),sort_keys=True,separators=(',',':')) for row in rows)
 doc={'schema_version':'osbench.stabilization.v1','trials':len(rows),'distinct_outcomes':len(signatures),'outcomes':[{'count':count,'value':json.loads(value)} for value,count in signatures.most_common()]}
 payload=json.dumps(doc,sort_keys=True,indent=2)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(payload)
 else:print(payload,end='')
 return 0
if __name__=='__main__':raise SystemExit(main())
