#include "../runtime/raw_syscall.h"
void _start(void) { char b; long r=sc3(SYS_read,-1,(long)&b,1); if(r!=-9) fail("invalid_fd"); ok("invalid_fd"); }
