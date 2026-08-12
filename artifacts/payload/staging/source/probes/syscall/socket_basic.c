#include "../runtime/raw_syscall.h"
void _start(void){ long s=osb_syscall3(OSB_SYS_socket,OSB_AF_UNIX,OSB_SOCK_STREAM,0); int ok=s>=0; if(ok)osb_syscall1(OSB_SYS_close,s); osb_result("socket_basic",ok); }
