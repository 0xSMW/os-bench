from __future__ import annotations
import pytest
from osbench.normalization import normalize_observation

@pytest.mark.parametrize('rule,key,value,expected',[
 ('pid','pid',123,'<PID>'),('ppid','ppid',1,'<PPID>'),('tid','tid',9,'<TID>'),('inode','inode',42,'<INODE>'),('ephemeral_port','port',54321,'<PORT>'),('addresses','address','0xabc','<ADDRESS>'),('host_metadata','hostname','host','<HOST>'),('timestamps','mtime',123,'<TIME>')])
def test_scalar_normalizers(rule,key,value,expected):
 c={'normalization':[rule],'observables':[]};assert normalize_observation({key:value},c)[key]==expected

def test_temporary_path():
 c={'normalization':['temporary_paths'],'observables':[]};assert normalize_observation({'p':'/tmp/osbench-abc/file'},c)['p']=='/tmp/<OSBENCH>/file'

def test_directory_order():
 c={'normalization':['directory_order'],'observables':[]};assert normalize_observation({'entries':['b','a']},c)['entries']==['a','b']

def test_duration_removed_when_unobserved():assert 'duration_ns' not in normalize_observation({'duration_ns':3},{'normalization':['none'],'observables':[]})

def test_duration_retained_when_observed():assert normalize_observation({'duration_ns':3},{'normalization':['none'],'observables':['timing']})['duration_ns']==3
