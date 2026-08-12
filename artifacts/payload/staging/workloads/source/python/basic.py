#!/usr/bin/env python3
import json,os,platform,threading
print(json.dumps({'pid_positive':os.getpid()>0,'python':platform.python_version(),'threads':threading.active_count()},sort_keys=True))
