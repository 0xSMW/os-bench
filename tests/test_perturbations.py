from osbench.perturbations import perturbation_selftest

def test_perturbations_detected():
 result=perturbation_selftest(12);assert result['passed'];assert len(result['perturbations'])==12
