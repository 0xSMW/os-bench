from osbench.syscalls import AMD64_SYSCALL_FAMILIES
def test_syscall_families_cover_core_surfaces():
 assert {'process','filesystem','memory','signal','ipc','network','polling','time'}<=AMD64_SYSCALL_FAMILIES.keys()
def test_high_value_calls_present():
 flat={x for v in AMD64_SYSCALL_FAMILIES.values() for x in v};assert {'execve','openat','mmap','futex','socket','epoll_wait'}<=flat
