#!/usr/bin/env python3
from __future__ import annotations
import json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2]
candidates=[pathlib.Path('/usr/include/x86_64-linux-gnu/asm/unistd_64.h'),pathlib.Path('/usr/include/asm/unistd_64.h')]
source=next((p for p in candidates if p.exists()),None)
rows=[]
if source:
 for line in source.read_text().splitlines():
  match=re.match(r'#define __NR_([A-Za-z0-9_]+)\s+(\d+)',line)
  if match:rows.append({'number':int(match.group(2)),'name':match.group(1),'family':'unclassified'})
else:
 fallback={'read':0,'write':1,'open':2,'close':3,'mmap':9,'munmap':11,'pipe':22,'clone':56,'fork':57,'execve':59,'exit':60,'wait4':61,'socket':41,'futex':202,'epoll_create1':291,'openat':257,'statx':332}
 rows=[{'number':number,'name':name,'family':'bootstrap'} for name,number in fallback.items()]
family_rules={'process':('clone','fork','exec','wait','exit','kill','getpid'),'file':('open','read','write','stat','link','unlink','rename','chmod','chown','mkdir','getdents','fsync'),'memory':('mmap','munmap','mprotect','brk','madvise','mlock'),'network':('socket','bind','listen','accept','connect','send','recv'),'sync':('futex','sem','eventfd'),'poll':('poll','select','epoll'),'time':('clock','timer','nanosleep','time')}
for row in rows:
 for family,prefixes in family_rules.items():
  if row['name'].startswith(prefixes):row['family']=family;break
doc={'schema_version':'osbench.syscall_inventory.v1','architecture':'x86_64','source':str(source) if source else 'fallback','count':len(rows),'syscalls':sorted(rows,key=lambda x:x['number'])}
path=ROOT/'data/syscalls-x86_64.json';path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(doc,sort_keys=True,indent=2)+'\n');print(json.dumps({'count':len(rows),'output':str(path)}))
