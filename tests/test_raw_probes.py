import json,platform,subprocess
from pathlib import Path
import pytest

def test_ten_locked_probe_binaries_exist():
 p=Path('artifacts/probes');bins=[x for x in p.iterdir() if x.is_file() and x.name not in {'SHA256SUMS','manifest.json'}];assert len(bins)==10

def test_probe_checksums_exist():assert Path('artifacts/probes/SHA256SUMS').is_file()
@pytest.mark.skipif(
 platform.system()!='Linux' or platform.machine() not in {'x86_64','AMD64'},
 reason='amd64 Linux probe binaries',
)
def test_raw_probes_execute():
 for p in sorted(Path('artifacts/probes').iterdir()):
  if not p.is_file() or p.name in {'SHA256SUMS','manifest.json'}:continue
  cp=subprocess.run([str(p)],capture_output=True,text=True,timeout=5);assert cp.returncode==0,(p,cp.stderr);assert '"status":"ok"' in cp.stdout
