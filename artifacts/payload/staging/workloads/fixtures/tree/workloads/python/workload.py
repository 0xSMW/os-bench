import hashlib,json,tempfile,pathlib
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'value'; p.write_text('osbench')
 print(json.dumps({'workload':'python','status':'ok','sha256':hashlib.sha256(p.read_bytes()).hexdigest()},sort_keys=True))
