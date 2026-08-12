#include "../runtime/raw_syscall.h"
void _start(void) { int word=0; long r=sc6(SYS_futex,(long)&word,FUTEX_WAKE,1,0,0,0); if(r<0) fail("futex"); ok("futex"); }
