#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,pathlib
import jsonschema
p=argparse.ArgumentParser();p.add_argument('proposal',type=pathlib.Path);args=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]
schema=json.loads((root/'tools/contract_discovery/proposal.schema.json').read_text())
doc=json.loads(args.proposal.read_text())
jsonschema.Draft202012Validator(schema).validate(doc)
print(json.dumps({'valid':True,'proposal_id':doc['proposal_id']},sort_keys=True))
