#include "../runtime/raw_syscall.h"
struct uts{char v[6][65];}; void _start(void){struct uts u;long r=osb_syscall1(OSB_SYS_uname,(long)&u);osb_result("uname_basic",r==0&&u.v[0][0]);}
