import json,subprocess,sys
from osbench.contracts import contracts_by_id
from osbench.dataset import generate_cases

def test_worker_protocol():
 c=contracts_by_id()['time.clock.monotonic'];case=generate_cases(profile='test',seed=1,cases_per_contract=1,contracts=[c])[0]
 cp=subprocess.run([sys.executable,'-m','osbench.probe_worker'],input=json.dumps(case)+'\n',capture_output=True,text=True,timeout=5);assert cp.returncode==0;r=json.loads(cp.stdout);assert r['status']=='ok';assert r['case_id']==case['case_id']
