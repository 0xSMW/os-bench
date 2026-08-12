#include "../runtime/raw_syscall.h"
struct statbuf { unsigned long data[32]; };
void _start(void) { struct statbuf s; long r=sc4(SYS_newfstatat,AT_FDCWD,(long)"/etc/os-release",(long)&s,0); if(r<0) fail("stat"); ok("stat"); }
