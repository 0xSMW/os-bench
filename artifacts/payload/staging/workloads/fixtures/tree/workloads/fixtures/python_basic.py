#!/usr/bin/env python3
import json, os, sqlite3, threading
print(json.dumps({"pid_positive":os.getpid()>0,"sqlite":sqlite3.sqlite_version,"threads":threading.active_count()},sort_keys=True))
