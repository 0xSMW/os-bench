from __future__ import annotations
import pytest
from osbench.comparators import compare

@pytest.mark.parametrize('reference,candidate,equivalence,expected',[
 ({'x':1},{'x':1},{'type':'exact'},True),({'x':1},{'x':2},{'type':'semantic'},False),([1,2],[2,1],{'type':'set'},True),([1,1,2],[1,2,2],{'type':'multiset'},False),(1.0,1.1,{'type':'range','tolerance':.2},True),(1.0,2.0,{'type':'range','tolerance':.2},False)])
def test_compare(reference,candidate,equivalence,expected):assert compare(reference,candidate,equivalence)[0] is expected
