from osbench.dataset import generate_cases
from osbench.oracle import select_cases

def test_shards_are_disjoint_and_complete():
 c=generate_cases(profile='test',seed=1,cases_per_contract=1);parts=[select_cases(c,shard_count=7,shard_index=i) for i in range(7)];ids=[{x['case_id'] for x in p} for p in parts];assert sum(map(len,ids))==len(c);assert len(set().union(*ids))==len(c)
def test_one_per_contract():
 c=generate_cases(profile='test',seed=1,cases_per_contract=3);s=select_cases(c,one_per_contract=True);assert len(s)==266;assert len({x['contract'] for x in s})==266
