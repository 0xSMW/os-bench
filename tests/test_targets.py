from osbench.targets import LocalTarget

def test_local_transport_support():
 t=LocalTarget();assert t.supports({'transport':'host'});assert t.supports({'transport':'raw_syscall'});assert not t.supports({'transport':'guest_agent'})
