from __future__ import annotations
from osbench.results import validate_results,summarize

def test_checked_in_results_validate(root):
 for name in ['isolated-smoke-final.json','eval-reference-local-final.json','full-local-selftest-final.json']:
  assert validate_results(root/'results'/name)['valid']

def test_summary_has_scores(root):
 result=summarize(root/'results/isolated-smoke-final.json');assert 'OSCorrect' in result;assert 'ObservedCorrect' in result
