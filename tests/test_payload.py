from __future__ import annotations
from osbench.payload import stage_payload,validate_payload_tree

def test_payload_stage_and_validate(tmp_path):
 result=stage_payload(tmp_path/'payload'); assert result['files']>=20; assert validate_payload_tree(tmp_path/'payload')['valid']

def test_payload_manifest_digest_detects_change(tmp_path):
 stage_payload(tmp_path/'payload');(tmp_path/'payload/source/probes/changed').write_text('x');assert not validate_payload_tree(tmp_path/'payload')['valid']
