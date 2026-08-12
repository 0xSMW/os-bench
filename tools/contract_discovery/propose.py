#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys

def main() -> int:
    parser=argparse.ArgumentParser(description='Create a deterministic Contract-proposal envelope from bounded evidence')
    parser.add_argument('evidence',type=pathlib.Path)
    parser.add_argument('--contract-id',required=True)
    parser.add_argument('--output',type=pathlib.Path)
    args=parser.parse_args()
    evidence=json.loads(args.evidence.read_text())
    if not isinstance(evidence,list) or not evidence: raise SystemExit('evidence must be a nonempty JSON array')
    digest=hashlib.sha256(json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    domain=args.contract_id.split('.',1)[0]
    document={
      'schema_version':'osbench.contract_proposal.v1',
      'proposal_id':f'{args.contract_id}:{digest[:16]}',
      'evidence':evidence,
      'contract':{
        'schema_version':'osbench.contract.v1','id':args.contract_id,'title':args.contract_id.replace('.',' ').replace('_',' ').title(),
        'domain':domain,'level':'kernel_subsystems','abstraction':domain,'operation':args.contract_id.split('.',1)[1],
        'description':'PROPOSED: replace with evidence-grounded observable behavior before review.',
        'prerequisites':[],'sources':[],'observables':['syscall_return','errno'],'normalization':['none'],
        'equivalence':{'type':'semantic'},'invariants':['Pending oracle execution and human review.'],'error_conditions':[],
        'case_dimensions':['primitive','boundary','failure','composition'],'orthogonal_with':[],'fault_injection':['invalid_argument'],
        'generator':{'implementation':'generators.common.contract_case','version':'1','parameters':{'contract_id':args.contract_id},'probe':'generic'},
        'timeouts':{'case_seconds':20},'transport':'guest_agent','tags':['draft','behavioral']
      },
      'uncertainty':{'confidence':0.0,'open_questions':['Exact reference behavior has not been measured.','Prerequisite closure remains to be established.']},
      'review_state':'proposed'
    }
    payload=json.dumps(document,sort_keys=True,indent=2)+'\n'
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(payload)
    else: sys.stdout.write(payload)
    return 0
if __name__=='__main__':raise SystemExit(main())
