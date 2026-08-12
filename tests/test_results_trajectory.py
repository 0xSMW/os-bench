from __future__ import annotations
from osbench.results import validate_results
from osbench.trajectory import TrajectoryRecorder,summarize_trajectory

def test_existing_result_valid(root):assert validate_results(root/'results/isolated-smoke-final.json')['valid']

def test_trajectory_roundtrip(tmp_path):
 r=TrajectoryRecorder.create(path=tmp_path/'t.json',run_id='test');r.append('build_started');r.append('contracts_passed',contracts_passed=3);s=summarize_trajectory(r.path);assert s['events']==2;assert s['last']['contracts_passed']==3
