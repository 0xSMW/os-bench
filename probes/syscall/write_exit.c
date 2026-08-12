#include "../runtime/raw_syscall.h"
void _start(void) { long r=sc3(SYS_write,1,(long)"raw-write-ok\n",13); if(r!=13) fail("write_exit"); ok("write_exit"); }
