#include "../runtime/raw_syscall.h"
void _start(void){long p=osb_syscall0(OSB_SYS_getpid);osb_result("getpid_basic",p>0);}
