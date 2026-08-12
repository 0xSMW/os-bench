from pathlib import Path
from osbench.inventory import collect_reference

def test_inventory_writes_manifest(tmp_path):
 r=collect_reference(tmp_path);assert r['schema_version']=='osbench.inventory.v1';assert (tmp_path/'manifest.json').is_file();assert (tmp_path/'packages.tsv').is_file()
