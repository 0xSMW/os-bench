from __future__ import annotations
import collections
import pytest
from osbench.constants import LEVELS
from osbench.dataset import PUBLIC_FAMILY_COUNTS,check_determinism,dataset_paths,generate_cases,validate_dataset
from osbench.util import jsonl_load,read_json,sha256_file

CASES=jsonl_load(dataset_paths('public')[0])


def test_case_count():assert len(CASES)==2660

def test_case_ids_unique():assert len({c['case_id'] for c in CASES})==2660

def test_ten_cases_per_contract():assert set(collections.Counter(c['contract'] for c in CASES).values())=={10}

def test_public_family_counts():assert collections.Counter(c['family'] for c in CASES)==PUBLIC_FAMILY_COUNTS

def test_dataset_validates():assert validate_dataset()['valid']

def test_dataset_deterministic():assert check_determinism(profile='public',seed=1,cases_per_contract=10)

def test_manifest_hash():
 case_path,manifest_path=dataset_paths('public');m=read_json(manifest_path);assert m['cases_sha256']==sha256_file(case_path)

@pytest.mark.parametrize('level',LEVELS)
def test_level_has_cases(level):assert any(c['level']==level for c in CASES)

@pytest.mark.parametrize('case',CASES[:40],ids=lambda c:c['case_id'])
def test_case_shape(case):
 assert case['schema_version']=='osbench.case.v1';assert case['transport'];assert case['stimulus']['token'];assert case['timeout_seconds']>0
