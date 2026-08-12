#!/usr/bin/env python3
import hashlib, json, os, pathlib, tempfile
with tempfile.TemporaryDirectory(prefix="osbench-fs-") as tmp:
    root=pathlib.Path(tmp); p=root/"value"; p.write_bytes(b"osbench")
    q=root/"hard"; os.link(p,q); r=root/"renamed"; p.rename(r)
    print(json.dumps({"status":"ok","same_inode":r.stat().st_ino==q.stat().st_ino,"sha256":hashlib.sha256(r.read_bytes()).hexdigest()}))
