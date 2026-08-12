#!/usr/bin/env python3
import json,threading
lock=threading.Lock();value=[0]
def worker():
 for _ in range(10000):
  with lock:value[0]+=1
threads=[threading.Thread(target=worker) for _ in range(4)]
[x.start() for x in threads];[x.join() for x in threads]
print(json.dumps({"status":"ok","value":value[0]}))
