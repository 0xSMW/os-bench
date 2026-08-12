from osbench.oracle import aggregate_contract_results,select_cases,load_public_cases

def test_aggregate():
 r=aggregate_contract_results([{'contract':'a','case_id':'1','passed':True},{'contract':'a','case_id':'2','passed':False}]);assert r['a']['pass_rate']==.5;assert not r['a']['passed']
def test_public_cases_load():assert len(load_public_cases())==2660
def test_public_one_per_contract():assert len(select_cases(load_public_cases(),one_per_contract=True))==266
