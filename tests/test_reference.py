from __future__ import annotations
import json
from osbench.reference import preflight_reference

def test_reference_lock_source(root):
 lock=json.loads((root/'reference/lock.json').read_text());assert lock['source']['sha256']=='e97736b7f49af22497c8df95e381ea5025faf3575af4b7ca6d5f40971265364e';assert lock['source']['size_bytes']==3992977408

def test_preflight_is_read_only():
 report=preflight_reference();assert report['schema_version']=='osbench.reference_preflight.v1';assert 'next_action' in report
