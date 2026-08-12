from __future__ import annotations
import pytest
from osbench.graph import build_graph,contracts_for_workload,prerequisites,unlocked_by,workloads_for,write_graph_outputs
from osbench.util import read_yaml

WORKLOADS=sorted(read_yaml(__import__('pathlib').Path(__file__).resolve().parents[1]/'capability_graph/workloads.yaml'))

def test_graph_counts():
 g=build_graph();assert len(g['nodes'])==266;assert len(g['edges'])==503

def test_root_prerequisites_empty():assert prerequisites('boot.firmware.uefi_entry')==[]

def test_root_unlocks_something():assert unlocked_by('boot.firmware.uefi_entry')

def test_transitive_prerequisites():assert 'boot.firmware.uefi_entry' in prerequisites('full.install_serve_reboot')

def test_graph_outputs():
 r=write_graph_outputs();assert r['acyclic'];assert r['nodes']==266;assert r['edges']==503

@pytest.mark.parametrize('workload',WORKLOADS)
def test_workload_closure(workload):
 closure=contracts_for_workload(workload);assert closure;assert all(isinstance(x,str) for x in closure)

@pytest.mark.parametrize('contract_id',['sync.futex.wait_wake','fs.file.write.basic','process.fork.basic','package.deb.install'])
def test_workloads_for_contract(contract_id):assert isinstance(workloads_for(contract_id),list)
