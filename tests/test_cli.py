from __future__ import annotations
import os,subprocess,sys

def run(root,*args):
 env={**os.environ,'PYTHONPATH':str(root/'src'),'OSBENCH_ROOT':str(root),'OSBENCH_REFERENCE_MODE':'local'};return subprocess.run([sys.executable,'-m','osbench',*args],cwd=root,env=env,capture_output=True,text=True,timeout=30)

def test_cli_contracts(root):assert run(root,'contracts','validate').returncode==0

def test_cli_dataset_validate(root):assert run(root,'dataset','validate').returncode==0

def test_cli_graph_query(root):
 cp=run(root,'graph','prerequisites','fs.file.write.basic');assert cp.returncode==0;assert 'boot.firmware.uefi_entry' in cp.stdout
