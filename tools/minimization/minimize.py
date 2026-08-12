#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,pathlib,subprocess,tempfile

def fails(command:str,sequence:list[object])->bool:
 with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:json.dump(sequence,f);path=f.name
 try:return subprocess.run(command.replace('{input}',path),shell=True).returncode!=0
 finally:pathlib.Path(path).unlink(missing_ok=True)

def ddmin(sequence:list[object],command:str)->list[object]:
 n=2
 while len(sequence)>=2:
  size=(len(sequence)+n-1)//n;reduced=False
  for start in range(0,len(sequence),size):
   candidate=sequence[:start]+sequence[start+size:]
   if candidate and fails(command,candidate):sequence=candidate;n=max(2,n-1);reduced=True;break
  if not reduced:
   if n>=len(sequence):break
   n=min(len(sequence),n*2)
 return sequence

def main()->int:
 p=argparse.ArgumentParser(description='Delta-debug an ordered JSON operation sequence')
 p.add_argument('input',type=pathlib.Path);p.add_argument('--command',required=True,help='Shell command containing {input}; nonzero means failure persists');p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 sequence=json.loads(a.input.read_text());minimum=ddmin(sequence,a.command);a.output.write_text(json.dumps(minimum,sort_keys=True,indent=2)+'\n');print(json.dumps({'before':len(sequence),'after':len(minimum),'output':str(a.output)}));return 0
if __name__=='__main__':raise SystemExit(main())
