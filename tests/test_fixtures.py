from pathlib import Path
def test_repository_has_expected_surfaces():
 for p in ['contracts','capability_graph','src/osbench','probes','workloads','reference','dataset/public/v0.1','tools','docs','harness','generators']:assert Path(p).is_dir()
def test_dataset_and_graph_are_materialized():
 assert Path('dataset/public/v0.1/cases.jsonl').stat().st_size>100000;assert Path('capability_graph/graph.yaml').stat().st_size>10000
