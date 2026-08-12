from __future__ import annotations
from osbench.trajectory import TrajectoryRecorder,summarize_trajectory

def test_trajectory_roundtrip(tmp_path):
 recorder=TrajectoryRecorder.create(tmp_path/'trajectory.json',run_id='test');recorder.append('build',attempt=1);recorder.append('test',passed=True);summary=summarize_trajectory(tmp_path/'trajectory.json');assert summary['events']==2;assert summary['event_types']==['build','test']
