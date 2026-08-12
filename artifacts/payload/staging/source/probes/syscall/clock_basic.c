#include "../runtime/raw_syscall.h"
struct ts{long sec;long nsec;}; void _start(void){struct ts t={0,0}; long r=osb_syscall2(OSB_SYS_clock_gettime,1,(long)&t);osb_result("clock_basic",r==0&&t.sec>=0&&t.nsec>=0);}
