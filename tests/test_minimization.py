from osbench.minimization import minimize_sequence

def test_sequence_minimization():
 result=minimize_sequence([1,2,3,4],lambda values:3 in values);assert result==[3]
