#include "../runtime/raw_syscall.h"
void _start(void) { long fd=sc3(SYS_socket,AF_INET,SOCK_STREAM,0); if(fd<0) fail("socket"); sc1(SYS_close,fd); ok("socket"); }
