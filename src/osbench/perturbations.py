from __future__ import annotations
import copy
from .comparators import compare

def perturbation_selftest(limit:int=12)->dict:
    baseline={"status":"ok","return":0,"errno":0,"stdout":"ok","observations":{"value":1,"entries":["a","b"]}}
    mutations=[]
    for i in range(limit):
        m=copy.deepcopy(baseline)
        if i%4==0:m['return']=1
        elif i%4==1:m['stdout']='bad'
        elif i%4==2:m['observations']['value']=2
        else:m['observations']['entries'].append('c')
        ok,diff=compare(baseline,m,{"type":"exact"});mutations.append({"index":i,"detected":not ok,"difference":diff})
    return {"passed":all(x['detected'] for x in mutations),"perturbations":mutations}
