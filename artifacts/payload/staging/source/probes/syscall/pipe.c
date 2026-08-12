#include "../runtime/raw_syscall.h"
void _start(void) { int f[2]; char b=0; if(sc1(SYS_pipe,(long)f)<0) fail("pipe"); if(sc3(SYS_write,f[1],(long)"q",1)!=1) fail("pipe"); if(sc3(SYS_read,f[0],(long)&b,1)!=1 || b!='q') fail("pipe"); sc1(SYS_close,f[0]); sc1(SYS_close,f[1]); ok("pipe"); }
