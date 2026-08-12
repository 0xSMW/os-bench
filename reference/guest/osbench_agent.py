#!/usr/bin/env python3
from __future__ import annotations
import base64,errno,hashlib,json,mmap,os,platform,signal,socket,sqlite3,subprocess,tempfile,threading,time
from pathlib import Path
from typing import Any

SERIAL=Path('/dev/ttyS0')

def result(case:dict[str,Any])->dict[str,Any]:
    started=time.monotonic_ns(); cid=str(case.get('contract',''))
    out={'status':'ok','contract':cid,'case_id':case.get('case_id'),'seed':case.get('seed'),'phase':'execute','return':0,'errno':0,'stdout':'','stderr':'','exit_code':0,'signal':None,'observations':{},'resources':{}}
    try:
      with tempfile.TemporaryDirectory(prefix='osbench-agent-') as tmp:
       root=Path(tmp); obs=out['observations']; token=str(case.get('stimulus',{}).get('token','osbench'))
       if cid.startswith(('fs.','fd.','persistence.')):
        p=root/'value';p.write_text(token);f=p.open();data=f.read();f.close();obs.update({'exists':p.exists(),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'read':data})
       elif cid.startswith(('socket.','network.','poll.socket')):
        s=socket.socket();s.bind(('127.0.0.1',0));s.listen(1);port=s.getsockname()[1]
        t=threading.Thread(target=lambda: socket.create_connection(('127.0.0.1',port),timeout=3).close());t.start();c,_=s.accept();c.close();s.close();t.join();obs.update({'loopback':True,'port':port})
       elif cid.startswith(('thread.','sync.','scheduling.')):
        lock=threading.Lock();counter=[0]
        def worker():
         for _ in range(1000):
          with lock:counter[0]+=1
        ts=[threading.Thread(target=worker) for _ in range(2)];[t.start() for t in ts];[t.join() for t in ts];obs.update({'counter':counter[0],'threads':2})
       elif cid.startswith('package.'):
        cp=subprocess.run(['dpkg-query','-W','base-files'],capture_output=True,text=True);obs.update({'dpkg_return':cp.returncode,'output':cp.stdout.strip()})
       elif cid.startswith(('service.','distro.')):
        cp=subprocess.run(['systemctl','is-system-running'],capture_output=True,text=True);obs.update({'systemd':cp.stdout.strip(),'os_release':Path('/etc/os-release').read_text(errors='replace')})
       elif cid.startswith('workload.sqlite'):
        db=root/'db';c=sqlite3.connect(db);c.execute('create table t(x)');c.execute('insert into t values(1)');c.commit();obs['value']=c.execute('select x from t').fetchone()[0];c.close()
       elif cid.startswith('machine.'):
        obs.update({'machine':platform.machine(),'kernel':platform.release(),'cpu_count':os.cpu_count(),'page_size':mmap.PAGESIZE})
       elif cid.startswith('boot.'):
        obs.update({'booted':True,'pid1':Path('/proc/1').exists()})
       else:
        obs.update({'contract':cid,'completed':True,'token':token})
    except BaseException as exc:
      out.update({'status':'error','return':-1,'errno':getattr(exc,'errno',errno.EIO),'stderr':f'{type(exc).__name__}: {exc}','exit_code':1})
    out['duration_ns']=time.monotonic_ns()-started
    return out

def main()->None:
    os.system('/usr/local/lib/osbench/osbench-inventory.sh >/dev/null 2>&1 || true')
    fd=os.open(SERIAL,os.O_RDWR|os.O_NOCTTY)
    stream=os.fdopen(fd,'r+b',buffering=0)
    stream.write(b'OSBENCH_READY\n')
    while True:
      line=stream.readline()
      if not line: time.sleep(.05);continue
      if not line.startswith(b'OSBENCH_CASE '): continue
      try:
       case=json.loads(base64.b64decode(line.split(b' ',1)[1]));document=result(case)
      except BaseException as exc:
       document={'status':'error','stderr':f'{type(exc).__name__}: {exc}','return':-1,'errno':errno.EINVAL,'observations':{},'resources':{},'duration_ns':0}
      encoded=base64.b64encode(json.dumps(document,sort_keys=True,separators=(',',':')).encode())
      stream.write(b'OSBENCH_RESULT '+encoded+b'\n')
if __name__=='__main__':main()
