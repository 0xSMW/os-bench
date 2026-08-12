from __future__ import annotations

import platform,shutil,subprocess

import pytest

@pytest.mark.parametrize('relative,args',[
 ('artifacts/workloads/static-elf',[]),('artifacts/workloads/dynamic-elf',['alpha']),('artifacts/workloads/pthread',[]),('artifacts/workloads/fixtures/shell_script.sh',[]),('artifacts/workloads/fixtures/python_basic.py',[]),('artifacts/workloads/fixtures/tcp_loopback.py',[]),('artifacts/workloads/fixtures/http_loopback.py',[])])
def test_built_workload(relative,args,root):
 if relative in {
  'artifacts/workloads/static-elf',
  'artifacts/workloads/dynamic-elf',
  'artifacts/workloads/pthread',
 } and (platform.system()!='Linux' or platform.machine() not in {'x86_64','AMD64'}):
  pytest.skip('amd64 Linux workload binary')
 path=root/relative;assert path.exists();cp=subprocess.run([str(path),*args],cwd=root,capture_output=True,text=True,timeout=10);assert cp.returncode==0,(cp.stdout,cp.stderr)

def test_package_fixtures(root):
 if shutil.which('dpkg-deb') is None:pytest.skip('dpkg-deb is required')
 packages=sorted((root/'artifacts/packages/repository').glob('*.deb'));assert len(packages)==2
 for package in packages:
  cp=subprocess.run(['dpkg-deb','--info',str(package)],capture_output=True,text=True);assert cp.returncode==0
