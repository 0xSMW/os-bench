from __future__ import annotations

import hashlib,json,pathlib,shutil,subprocess

import pytest

def test_package_lock_matches_artifacts(root):
 lock=json.loads((root/'workloads/packages/lock.json').read_text()); assert len(lock['packages'])==2
 for item in lock['packages']:
  path=root/'artifacts/packages/repository'/item['filename'];assert path.is_file();assert path.stat().st_size==item['size'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']

def test_package_metadata(root):
 if shutil.which('dpkg-deb') is None:pytest.skip('dpkg-deb is required')
 path=root/'artifacts/packages/repository/osbench-hello_0.1.0_all.deb';out=subprocess.run(['dpkg-deb','-f',path,'Package','Version','Architecture'],capture_output=True,text=True,check=True).stdout;assert 'osbench-hello' in out;assert '0.1.0' in out;assert 'all' in out
