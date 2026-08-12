from __future__ import annotations
from osbench.contracts import contracts_by_id
from osbench.scoring import score_results


def test_empty_score_zero():
 s=score_results([],contracts_by_id(),profile='macos_tcg');assert s['OSCorrect']==0;assert s['Depth90'] is None

def test_partial_score_not_authoritative_perfect():
 cid='boot.firmware.uefi_entry';s=score_results([{'contract':cid,'passed':True}],contracts_by_id(),profile='macos_tcg');assert s['OSCorrect']==0;assert s['ObservedCorrect']==1

def test_native_suppressed_on_tcg():
 s=score_results([],contracts_by_id(),profile='macos_tcg');assert s['Native_1'] is None;assert s['Native_2'] is None
