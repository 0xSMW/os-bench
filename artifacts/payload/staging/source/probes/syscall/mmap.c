#include "../runtime/raw_syscall.h"
void _start(void) { long p=sc6(SYS_mmap,0,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0); if(p<0) fail("mmap"); ((volatile char*)p)[0]='x'; if(((volatile char*)p)[0]!='x') fail("mmap"); sc2(SYS_munmap,p,4096); ok("mmap"); }
