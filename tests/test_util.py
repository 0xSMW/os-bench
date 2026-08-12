from __future__ import annotations
import pathlib
from osbench.util import jsonl_load,jsonl_write,read_json,read_yaml,sha256_file,sha256_tree,sha256_value,stable_json,write_json,write_yaml

def test_stable_json_order(): assert stable_json({'b':1,'a':2})=='{"a":2,"b":1}'

def test_value_hash_stable(): assert sha256_value({'a':1})==sha256_value({'a':1})

def test_json_roundtrip(tmp_path):
 p=tmp_path/'a.json';write_json(p,{'x':1});assert read_json(p)=={'x':1}

def test_yaml_roundtrip(tmp_path):
 p=tmp_path/'a.yaml';write_yaml(p,{'x':[1,2]});assert read_yaml(p)=={'x':[1,2]}

def test_jsonl_roundtrip(tmp_path):
 p=tmp_path/'a.jsonl';jsonl_write(p,[{'x':1},{'x':2}]);assert jsonl_load(p)==[{'x':1},{'x':2}]

def test_file_hash_changes(tmp_path):
 p=tmp_path/'f';p.write_text('a');a=sha256_file(p);p.write_text('b');assert sha256_file(p)!=a

def test_tree_hash_stable(tmp_path):
 (tmp_path/'a').write_text('a');assert sha256_tree(tmp_path)==sha256_tree(tmp_path)

def test_tree_hash_exclusion(tmp_path):
 (tmp_path/'a').write_text('a');(tmp_path/'skip').mkdir();(tmp_path/'skip/b').write_text('b');assert sha256_tree(tmp_path,exclude=('skip',))

def test_tree_hash_ignores_python_bytecode(tmp_path):
 (tmp_path/'module.py').write_text('value = 1\n');expected=sha256_tree(tmp_path)
 cache=tmp_path/'__pycache__';cache.mkdir();(cache/'module.cpython-313.pyc').write_bytes(b'cache')
 assert sha256_tree(tmp_path)==expected
