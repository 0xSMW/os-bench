from __future__ import annotations
import collections
import pytest
from osbench.constants import LEVELS
from osbench.contracts import contract_files,contracts_by_id,load_contracts,validate_contracts

CONTRACTS=load_contracts()


def test_contract_corpus_is_valid():
 report=validate_contracts();assert report.valid,report.issues

def test_contract_count():assert len(CONTRACTS)==266

def test_contract_ids_unique():assert len(contracts_by_id(CONTRACTS))==266

def test_contract_file_count():assert len(contract_files())==266

def test_level_counts():
 expected={'boot':7,'machine':10,'linux_primitives':17,'kernel_subsystems':99,'linux_process_environment':22,'posix_userspace':15,'linux_system':34,'distro':26,'package_ecosystem':13,'real_workloads':16,'full_reconstruction':7}
 assert collections.Counter(c['level'] for c in CONTRACTS)==expected

def test_all_levels_present():assert set(c['level'] for c in CONTRACTS)==set(LEVELS)

def test_single_root():
 roots=[c['id'] for c in CONTRACTS if not c['prerequisites']];assert roots==['boot.firmware.uefi_entry']

def test_edge_count():assert sum(len(c['prerequisites']) for c in CONTRACTS)==503

@pytest.mark.parametrize('contract',CONTRACTS,ids=lambda c:c['id'])
def test_contract_semantic_minimum(contract):
 assert contract['schema_version']=='osbench.contract.v1'
 assert contract['description'].strip()
 assert contract['invariants']
 assert contract['sources']
 assert contract['case_dimensions']
 assert contract['transport'] in {'none','serial','raw_syscall','guest_agent','shell','ssh','host'}
 assert all(dep!=contract['id'] for dep in contract['prerequisites'])
