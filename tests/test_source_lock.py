from osbench.source_lock import _measure
a=_measure(__import__('pathlib').Path('.').resolve())
def test_measure_has_core_hashes():assert a['contract_corpus_sha256'];assert a['evaluator_source_tree_sha256'];assert a['raw_probe_source_tree_sha256']
def test_hash_lengths():assert all(v is None or len(v)==64 for v in a.values())
