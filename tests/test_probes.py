from __future__ import annotations

import platform

import pytest

from osbench.contracts import load_contracts
from osbench.generators import generic_case
from osbench.probes import execute_case

HOST=[c for c in load_contracts() if c['transport']=='host']
SAMPLE=HOST[::max(1,len(HOST)//50)][:50]

@pytest.mark.parametrize('contract',SAMPLE,ids=lambda c:c['id'])
def test_host_probe_executes(contract):
 if contract['domain']=='procfs' and platform.system()!='Linux':pytest.skip('procfs requires Linux')
 case=generic_case(contract,seed=7,family='primitive',index=0,profile='test');result=execute_case(case);assert result['status']=='ok',result;assert result['contract']==contract['id']

def test_signal_probe_executes_from_worker_thread():
 import concurrent.futures
 contract=next(c for c in HOST if c['id']=='signal.delivery')
 case=generic_case(contract,seed=7,family='primitive',index=0,profile='test')
 with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:result=executor.submit(execute_case,case).result()
 assert result['status']=='ok',result
