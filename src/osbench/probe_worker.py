from __future__ import annotations
import json,sys
from .probes import execute_case

def main():
    for line in sys.stdin:
        try:
            case=json.loads(line);result=execute_case(case)
        except BaseException as exc:
            result={"status":"error","stderr":f"{type(exc).__name__}: {exc}"}
        print(json.dumps(result,sort_keys=True),flush=True)
if __name__=="__main__":main()
