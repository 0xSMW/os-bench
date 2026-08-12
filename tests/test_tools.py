from __future__ import annotations
import json,subprocess,sys

def test_syscall_inventory(root):
 d=json.loads((root/'data/syscalls-x86_64.json').read_text());assert d['architecture']=='x86_64';assert d['count']>=300

def test_contract_proposal_tool(tmp_path,root):
 evidence=tmp_path/'e.json';evidence.write_text('[{"kind":"trace","reference":"trace.json"}]');out=tmp_path/'p.json';cp=subprocess.run([sys.executable,str(root/'tools/contract_discovery/propose.py'),str(evidence),'--contract-id','fs.example.behavior','--output',str(out)],capture_output=True,text=True);assert cp.returncode==0,cp.stderr;assert json.loads(out.read_text())['review_state']=='proposed'
