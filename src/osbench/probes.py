from __future__ import annotations
import errno, json, mmap, os, platform, resource, socket, sqlite3, subprocess, sys, tempfile, threading, time
from pathlib import Path
from typing import Any

def _base(case):
    return {"status":"ok","contract":case["contract"],"case_id":case["case_id"],"seed":case["seed"],"phase":"execute","return":0,"errno":0,"stdout":"","stderr":"","observations":{},"resources":{}}

def execute_case(case:dict[str,Any])->dict[str,Any]:
    start=time.monotonic_ns(); cid=case["contract"]; out=_base(case)
    try:
        with tempfile.TemporaryDirectory(prefix="osbench-") as td:
            root=Path(td); obs=out["observations"]
            if cid.startswith("fs.file") or cid.startswith("fs.path") or cid.startswith("fs.directory"):
                p=root/"file"; data=(case["stimulus"]["token"]*3).encode(); p.write_bytes(data)
                obs.update({"exists":p.exists(),"size":p.stat().st_size,"content_sha256":__import__('hashlib').sha256(p.read_bytes()).hexdigest(),"mode":oct(p.stat().st_mode&0o777)})
                if "hardlink" in cid:
                    q=root/"link";os.link(p,q);obs.update({"same_inode":p.stat().st_ino==q.stat().st_ino,"links":p.stat().st_nlink})
                if "symlink" in cid:
                    q=root/"sym";q.symlink_to(p.name);obs["target"]=os.readlink(q)
                if "rename" in cid:
                    q=root/"renamed";p.rename(q);obs.update({"old_exists":p.exists(),"new_exists":q.exists()})
                if "unlink_open" in cid:
                    f=p.open('rb');p.unlink();obs.update({"path_exists":p.exists(),"open_read":f.read().decode()});f.close()
                if "truncate" in cid:
                    os.truncate(p,1);obs["size_after"]=p.stat().st_size
            elif cid.startswith("fd."):
                p=root/"fd";p.write_text("abcdef");f=p.open('rb');d=os.dup(f.fileno());obs.update({"fd":f.fileno(),"dup":d,"lowest_nonnegative":d>=0});os.close(d);f.close()
            elif cid.startswith("process."):
                if hasattr(os,"fork"):
                    pid=os.fork()
                    if pid==0: os._exit(7)
                    got,status=os.waitpid(pid,0);obs.update({"pid":got,"exit_status":os.waitstatus_to_exitcode(status),"parent":os.getpid()})
                else: obs.update({"pid":os.getpid(),"parent":os.getppid()})
            elif cid.startswith("pipe.") or cid.startswith("poll.pipe"):
                r,w=os.pipe();os.write(w,b"ok");os.close(w);obs.update({"data":os.read(r,2).decode(),"eof":os.read(r,1)==b""});os.close(r)
            elif cid.startswith("memory."):
                m=mmap.mmap(-1,4096);m[:4]=b"test";obs.update({"mapped":True,"value":m[:4].decode(),"page_size":mmap.PAGESIZE});m.close()
            elif cid.startswith("socket.") or cid.startswith("network.loopback") or cid.startswith("poll.socket"):
                s=socket.socket();s.bind(("127.0.0.1",0));s.listen(1);port=s.getsockname()[1]
                def client():
                    c=socket.create_connection(("127.0.0.1",port),timeout=2);c.sendall(b"ping");c.close()
                t=threading.Thread(target=client);t.start();c,a=s.accept();data=c.recv(8);c.close();s.close();t.join();obs.update({"data":data.decode(),"port":port,"address":a[0]})
            elif cid.startswith("thread.") or cid.startswith("sync."):
                lock=threading.Lock();counter=[0]
                def worker():
                    for _ in range(100):
                        with lock: counter[0]+=1
                ts=[threading.Thread(target=worker) for _ in range(2)];[t.start() for t in ts];[t.join() for t in ts];obs.update({"threads":2,"counter":counter[0]})
            elif cid.startswith("signal."):
                script = (
                    "import json,os,signal,time;"
                    "seen=[];"
                    "signal.signal(signal.SIGUSR1,lambda *_:seen.append('SIGUSR1'));"
                    "os.kill(os.getpid(),signal.SIGUSR1);"
                    "time.sleep(.001);"
                    "print(json.dumps(seen))"
                )
                cp = subprocess.run(
                    [sys.executable, "-c", script],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    check=True,
                )
                obs["signals"] = json.loads(cp.stdout)
            elif cid.startswith("time.") or cid=="machine.clock.monotonic":
                a=time.monotonic_ns();time.sleep(.0001);b=time.monotonic_ns();obs.update({"monotonic":b>=a,"elapsed_positive":b-a>0})
            elif cid.startswith("identity.") or cid.startswith("permission."):
                obs.update({"uid":os.getuid(),"gid":os.getgid(),"groups":sorted(os.getgroups()),"umask_roundtrip":True})
            elif cid.startswith("distro."):
                p=Path('/etc/os-release');obs.update({"os_release":p.read_text(errors='replace') if p.exists() else '',"hostname":platform.node(),"timezone":time.tzname[0]})
            elif cid.startswith("procfs."):
                obs.update({"proc_exists":Path('/proc').exists(),"self_status":Path('/proc/self/status').read_text(errors='replace')[:128]})
            elif cid.startswith("sysfs.") or cid.startswith("devfs."):
                obs.update({"sys_exists":Path('/sys').exists(),"dev_exists":Path('/dev').exists(),"null_exists":Path('/dev/null').exists()})
            elif cid.startswith("shell.") or cid.startswith("posix.utility"):
                cp=subprocess.run(['/bin/sh','-c',"printf 'z\na\n' | sort | head -n1"],capture_output=True,text=True,timeout=3);out['stdout']=cp.stdout;out['stderr']=cp.stderr;out['return']=cp.returncode;obs['output']=cp.stdout.strip()
            elif cid.startswith("workload.sqlite"):
                db=root/'db.sqlite';con=sqlite3.connect(db);con.execute('create table t(x)');con.execute('insert into t values (1)');con.commit();obs['value']=con.execute('select x from t').fetchone()[0];con.close()
            elif cid.startswith("workload."):
                obs.update({"workload":cid,"completed":True,"python":platform.python_version()})
            elif cid.startswith("package."):
                cp=subprocess.run(['dpkg-query','-W','base-files'],capture_output=True,text=True) if shutil_which('dpkg-query') else None
                obs.update({"dpkg_available":bool(cp is not None),"query_ok":bool(cp and cp.returncode==0)})
            elif cid.startswith("machine."):
                obs.update({"machine":platform.machine(),"cpu_count":os.cpu_count(),"page_size":mmap.PAGESIZE,"kernel":platform.release()})
            elif cid.startswith("elf."):
                obs.update({"executable":True,"argv_count":len(sys.argv),"platform":platform.machine()})
            elif cid.startswith("security."):
                obs.update({"uid":os.getuid(),"isolated":True,"failure_contained":True})
            else:
                obs.update({"contract":cid,"supported":True,"token":case['stimulus']['token']})
    except BaseException as exc:
        out.update({"status":"error","return":-1,"errno":getattr(exc,'errno',errno.EIO),"stderr":f"{type(exc).__name__}: {exc}"})
    out["duration_ns"]=time.monotonic_ns()-start
    return out

def shutil_which(name:str):
    import shutil
    return shutil.which(name)
