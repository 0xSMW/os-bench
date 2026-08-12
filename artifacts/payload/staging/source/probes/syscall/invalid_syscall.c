#include "../runtime/raw_syscall.h"
void _start(void){long r=osb_syscall0(999999);osb_result("invalid_syscall",r<0);}
