#include "../runtime/raw_syscall.h"
void _start(void) { long p=sc0(SYS_fork); if(p<0) fail("fork_wait"); if(p==0) finish(7); int st=0; long w=sc4(SYS_wait4,p,(long)&st,0,0); if(w!=p || ((st>>8)&255)!=7) fail("fork_wait"); ok("fork_wait"); }
